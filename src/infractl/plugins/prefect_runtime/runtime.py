"""ICL Prefect runtime implementation.

Environment variable PREFECT_API_URL needs to be set to the URL of a Prefect server running in the
cluster.

"""

import asyncio
import contextlib
import copy
import functools
import inspect
import os
import pathlib
import tempfile
from typing import Any, Dict, List, Optional, Union

import dynaconf
import prefect.blocks.core as blocks
import pydantic
from prefect import deployments, filesystems, settings
from prefect.client import orchestration
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.exceptions import ObjectAlreadyExists, ObjectNotFound
from prefect.server.api import server
from prefect.utilities.callables import parameter_schema

import infractl
import infractl.base
import infractl.fs
import infractl.identity
import infractl.plugins.prefect_runtime.utils as prefect_utils
from infractl import defaults
from infractl.logging import get_logger
from infractl.plugins import icl_infrastructure, prefect_runtime

logger = get_logger()


DEFAULT_ITEMS_TO_IGNORE = [
    # Prefect artifacts
    '.prefectignore',
    # Python artifacts
    '__pycache__/',
    '*.py[cod]',
    '*$py.class',
    '*.egg-info/',
    '*.egg',
    # Type checking artifacts
    '.mypy_cache/',
    '.dmypy.json',
    'dmypy.json',
    '.pyre/',
    # IPython
    'profile_default/',
    'ipython_config.py',
    '*.ipynb_checkpoints/*',
    # Environments
    '.python-version',
    '.env',
    '.venv',
    'env/',
    'venv/',
    '.conda/',
    # MacOS
    '.DS_Store',
    # Dask
    'dask-worker-space/',
    # Editors
    '.idea/',
    '.vscode/',
    '.vscode-server/',
]


class PrefectRuntimeError(Exception):
    """Prefect runtime error."""


class PrefectBlock(pydantic.BaseModel):
    """Prefect Block specification."""

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    kind: str
    name: str
    block: Optional[blocks.Block] = None

    @property
    def full_name(self):
        return f'{self.kind}/{self.name}'

    async def save(self, **kwargs):
        return await self.block.save(self.name, **kwargs)


class PrefectDeployment(pydantic.BaseModel):
    """Reference to a Prefect deployment.

    Prefect 3 removed `prefect.deployments.Deployment`, so this class keeps the deployment
    attributes required to run and identify a deployment.
    """

    id: Optional[Any] = None
    name: str
    flow_name: str

    @property
    def full_name(self):
        """Returns a deployment name as Prefect shows it: "{flow_name}/{deployment_name}"."""
        return f'{self.flow_name}/{self.name}'


class PrefectProgramRunner(infractl.base.Runnable):
    """Prefect program."""

    def __init__(
        self,
        prefect_client: orchestration.PrefectClient,
        prefect_deployment: PrefectDeployment,
    ):
        self.prefect_client = prefect_client
        self.prefect_deployment = prefect_deployment

    @property
    def deployment(self) -> PrefectDeployment:
        """Returns a Prefect deployment for this program."""
        return self.prefect_deployment

    async def cancel(self, flow_id):
        """Cancel a flow run by ID."""
        await prefect_utils.cancel(self.prefect_client, flow_id)

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> prefect_runtime.PrefectProgramRun:
        """Runs flow synchronously.

        Note that currently Prefect does not support returning the result.
        """

        # setting detach to True is the same as setting timeout to 0
        if detach:
            timeout = 0

        deployment_name = self.prefect_deployment.full_name
        logger.info('Running deployment "%s" with timeout="%s" seconds', deployment_name, timeout)
        flow_run = await deployments.run_deployment(
            name=deployment_name,
            parameters=parameters,
            client=self.prefect_client,
            timeout=timeout,
        )
        if not flow_run.state.is_final() and timeout not in (None, 0):
            logger.info('Cancel flow run "%s" by timeout="%s" seconds', flow_run.name, timeout)
            await self.cancel(flow_run.id)
            raise asyncio.exceptions.TimeoutError
        logger.info('FlowRun %s %s', flow_run.name, flow_run.state)
        return prefect_runtime.PrefectProgramRun(flow_run, self.prefect_client)


class PythonProgramRunner(PrefectProgramRunner):
    """Runs a Python program.

    TODO: potentially use types.MethodType to override `run` for the existing runner instance?
    """

    program: str
    entrypoint: Optional[str]
    runner: PrefectProgramRunner

    def __init__(
        self,
        runner: PrefectProgramRunner,
        program: str,
        entrypoint: Optional[str],
    ):
        super().__init__(runner.prefect_client, runner.prefect_deployment)
        self.runner = runner
        self.program = program
        self.entrypoint = entrypoint

    async def cancel(self, flow_id):
        """Cancels a flow run by ID."""
        await self.runner.cancel(flow_id)

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> prefect_runtime.PrefectProgramRun:
        """Runs flow."""
        if self.entrypoint:
            if parameters and not isinstance(parameters, Dict):
                raise ValueError('For a Python function parameters must be a dict')
        else:
            if parameters and not isinstance(parameters, List):
                raise ValueError('For a Python program parameters must be a list')

        flow_parameters = {
            'program': self.program,
            'entrypoint': self.entrypoint,
            'parameters': parameters,
        }
        return await self.runner.run(parameters=flow_parameters, timeout=timeout, detach=detach)


class PrefectRuntimeImplementation(
    infractl.base.RuntimeImplementation, registration_name='prefect'
):
    """Prefect runtime implementation."""

    # Custom settings to use instead of global infractl.base.SETTINGS
    _settings: Optional[dynaconf.Dynaconf] = None
    _files_block: str = ''
    _script: str = ''

    def __init__(
        self,
        runtime: Optional[infractl.base.runtime.Runtime] = None,
        infrastructure_implementation: Optional[infractl.base.InfrastructureImplementation] = None,
    ):
        if not isinstance(
            infrastructure_implementation, icl_infrastructure.IclInfrastructureImplementation
        ):
            raise NotImplementedError(
                f'{infrastructure_implementation.__class__.__name__} is not supported'
            )
        super().__init__(
            runtime=runtime, infrastructure_implementation=infrastructure_implementation
        )

    @functools.cached_property
    def prefect_client(self):
        """Returns Prefect client."""
        if self.prefect_api_url:
            return orchestration.PrefectClient(self.prefect_api_url)
        return orchestration.PrefectClient(server.create_app(ephemeral=True))

    @functools.cached_property
    def prefect_api_url(self) -> Optional[str]:
        """Returns Prefect API URL.

        If the infrastructure address is not set (empty string) or 'local' then this method returns
        None, which means that an ephemeral instance of Prefect will be used.
        """
        # TODO: support different schemas
        if (
            self.infrastructure_implementation.address
            and self.infrastructure_implementation.address != 'local'
        ):
            return f'http://prefect.{self.infrastructure_implementation.address}/api'
        return None

    async def deploy(
        self,
        program: infractl.base.Program,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[infractl.base.ManifestFilter] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Deploys a program."""

        program = prefect_runtime.load_program(path=program.path, name=program.name)

        with settings.temporary_settings(updates={settings.PREFECT_API_URL: self.prefect_api_url}):
            if isinstance(program, prefect_runtime.PythonProgram):
                return await self.deploy_python_program(
                    program,
                    customizations=customizations,
                    manifest_filter=manifest_filter,
                    name=name,
                    **kwargs,
                )
            else:
                return await self.deploy_prefect_program(
                    program,
                    customizations=customizations,
                    manifest_filter=manifest_filter,
                    name=name,
                    **kwargs,
                )

    async def deploy_python_program(
        self,
        program: prefect_runtime.PythonProgram,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[infractl.base.ManifestFilter] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> infractl.base.DeployedProgram:
        """Deploys a Python program wrapped in a Prefect flow."""
        # Running a Prefect wrapper for a Python program requires a custom runtime and a custom
        # runner.

        self.runtime = copy.copy(self.runtime)
        self.runtime.files = copy.copy(self.runtime.files)
        self.runtime.files.extend(program.files)

        deployed_program = await self.deploy_prefect_program(
            program,
            customizations=customizations,
            manifest_filter=manifest_filter,
            name=name,
            **kwargs,
        )
        deployed_program.runner = PythonProgramRunner(
            runner=deployed_program.runner,
            program=program.program,
            entrypoint=program.entrypoint,
        )

        return deployed_program

    async def deploy_prefect_program(
        self,
        program: prefect_runtime.PrefectProgram,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[infractl.base.ManifestFilter] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> infractl.base.DeployedProgram:
        """Deploys a Prefect program."""
        if not isinstance(program, prefect_runtime.PrefectProgram):
            raise NotImplementedError(f'PrefectProgram expected, got {program.__class__.__name__}')

        if customizations:
            raise PrefectRuntimeError(
                'customizations are not supported with Prefect 3: job manifest customization '
                'moved to the work pool base job template, '
                'see https://docs.prefect.io/v3/concepts/work-pools'
            )
        if manifest_filter:
            raise PrefectRuntimeError(
                'manifest_filter is not supported with Prefect 3: job manifest customization '
                'moved to the work pool base job template, '
                'see https://docs.prefect.io/v3/concepts/work-pools'
            )

        flow_file_name = pathlib.Path(program.path).name
        prefect_flow = program.flow
        # use a custom flow name if specified
        if name:
            # create a copy of the flow object with a new name to make sure to keep to original
            # object intact for the case it was imported as Python object.
            prefect_flow = prefect_flow.with_options(name=name)

        prefect_storage_block = await self.create_code_block(prefect_flow.name)

        # The first pull step downloads the program code, the following steps download the runtime
        # files, extract them to the code directory and make the code directory the working
        # directory for the flow run.
        pull_steps: List[Dict[str, Any]] = [
            {
                'prefect.deployments.steps.pull_with_block': {
                    'id': 'pull_code',
                    'block_type_slug': prefect_storage_block.kind,
                    'block_document_name': prefect_storage_block.name,
                },
            },
        ]
        if self.runtime.files:
            prefect_files_block = await self.create_files_block(prefect_flow.name)
            pull_steps.extend(
                [
                    {
                        'prefect.deployments.steps.pull_with_block': {
                            'id': 'pull_files',
                            'block_type_slug': prefect_files_block.kind,
                            'block_document_name': prefect_files_block.name,
                        },
                    },
                    {
                        # Both directories are relative to the working directory of the flow run
                        # pod, where this step is executed.
                        'prefect.deployments.steps.run_shell_script': {
                            'script': (
                                f'bash "{{{{ pull_files.directory }}}}/{self._script}"'
                                ' "{{ pull_code.directory }}"'
                            ),
                        },
                    },
                    {
                        'prefect.deployments.steps.set_working_directory': {
                            'directory': '{{ pull_code.directory }}',
                        },
                    },
                ]
            )

        prefect_default_storage_block = await self.create_result_block('prefect-persistent-results')
        logger.info('Default result storage block: "%s"', prefect_default_storage_block)

        await self.upload_code(prefect_storage_block, pathlib.Path(program.path).absolute().parent)

        work_pool_name = self.settings('prefect_work_pool', 'default-pool')
        await self.ensure_work_pool(work_pool_name)

        # pass through kwargs that are valid arguments for creating a Prefect deployment
        create_deployment_parameters = set(
            inspect.signature(orchestration.PrefectClient.create_deployment).parameters
        ) - {'self', 'flow_id', 'name', 'entrypoint', 'pull_steps', 'job_variables'}
        deployment_kwargs = {
            key: value for key, value in kwargs.items() if key in create_deployment_parameters
        }
        deployment_kwargs.setdefault('work_queue_name', self.settings('prefect_queue', 'prod'))

        flow_id = await self.prefect_client.create_flow(prefect_flow)
        deployment_id = await self.prefect_client.create_deployment(
            flow_id=flow_id,
            # Note that Prefect shows deployments as "{flow_name}/{deployment_name}".
            name=program.deployment_name,
            entrypoint=f'{flow_file_name}:{prefect_flow.fn.__name__}',
            work_pool_name=work_pool_name,
            pull_steps=pull_steps,
            job_variables=self.job_variables(prefect_default_storage_block),
            parameter_openapi_schema=parameter_schema(prefect_flow).model_dump_for_openapi(),
            **deployment_kwargs,
        )

        prefect_deployment = PrefectDeployment(
            id=deployment_id,
            name=program.deployment_name,
            flow_name=prefect_flow.name,
        )

        return infractl.base.DeployedProgram(
            program=program,
            runner=PrefectProgramRunner(self.prefect_client, prefect_deployment),
        )

    async def ensure_work_pool(self, name: str) -> None:
        """Makes sure the work pool exists.

        In an ICL cluster the work pool is created by the Prefect worker. This method creates the
        work pool for the case when infractl is used with a standalone or ephemeral Prefect server.
        """
        try:
            await self.prefect_client.read_work_pool(name)
        except ObjectNotFound:
            with contextlib.suppress(ObjectAlreadyExists):
                await self.prefect_client.create_work_pool(
                    WorkPoolCreate(name=name, type='kubernetes')
                )

    async def upload_code(self, block: PrefectBlock, path: pathlib.Path) -> None:
        """Uploads the program directory to the code storage block."""
        ignore_file_name: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as ignore_file:
                ignore_file_name = ignore_file.name
                ignore_file.write('\n'.join(DEFAULT_ITEMS_TO_IGNORE).encode('utf-8'))
                ignore_file.flush()
                ignore_file.close()
                await block.block.put_directory(
                    local_path=str(path),
                    ignore_file=ignore_file_name,
                )
        finally:
            if ignore_file_name:
                with contextlib.suppress(FileNotFoundError):
                    os.remove(ignore_file_name)

    def job_variables(
        self, default_result_storage_block: Optional[PrefectBlock] = None
    ) -> Dict[str, Any]:
        """Returns job variables for a Prefect deployment.

        Job variables override the variables in the work pool base job template. The default
        Kubernetes work pool template supports "image", "env", "command" and a few others,
        see https://docs.prefect.io/v3/concepts/work-pools.
        """
        if self.infrastructure_implementation.gpus:
            raise PrefectRuntimeError(
                'gpus are not supported with Prefect 3: add the GPU resource limits to the work '
                'pool base job template, see https://docs.prefect.io/v3/concepts/work-pools'
            )
        if self.settings('prefect_shared_volume_mount'):
            raise PrefectRuntimeError(
                'prefect_shared_volume_mount is not supported with Prefect 3: add the volume to '
                'the work pool base job template, '
                'see https://docs.prefect.io/v3/concepts/work-pools'
            )

        env = self.runtime.environment.copy() if self.runtime.environment else {}

        # TODO: support different targets runtime dependencies, such as using a custom docker image
        if self.runtime.dependencies.pip:
            # TODO: check if environment variable EXTRA_PIP_PACKAGES is set and merge if necessary
            env['EXTRA_PIP_PACKAGES'] = ' '.join(self.runtime.dependencies.pip)

        if default_result_storage_block:
            env['PREFECT_DEFAULT_RESULT_STORAGE_BLOCK'] = default_result_storage_block.full_name

        variables: Dict[str, Any] = {'env': env}

        # TODO: move the default image to discover
        image = self.settings('prefect_image', defaults.PREFECT_IMAGE)
        if image:
            variables['image'] = image

        return variables

    @functools.cached_property
    def remote_storage_settings(self):
        """Gets storage settings for Prefect RemoteFileSystem."""
        storage_settings = self.settings('prefect_storage_fsspec', {})
        storage_settings.setdefault('key', 'x1miniouser')
        storage_settings.setdefault('secret', 'x1miniopass')
        storage_settings.setdefault('use_ssl', False)
        client_kwargs = storage_settings.setdefault('client_kwargs', {})
        if 'endpoint_url' not in client_kwargs:
            # TODO: support different schemas
            client_kwargs['endpoint_url'] = (
                f'http://s3.{self.infrastructure_implementation.address}'
            )
        return storage_settings

    def sanitize_block_name(self, block_name: str) -> str:
        """Removes unallowable characters in a prefect document block name."""
        return block_name.replace('_', '-')

    def define_storage_block(self, base_path: str, block_name: str) -> PrefectBlock:
        """Defines Prefect storage block.

        The following Prefect storage blocks are supported:
        * LocalFileSystem (scheme is "file")
        * RemoteFileSystem (scheme is not "file")
        """
        block_name = self.sanitize_block_name(block_name)
        if base_path.startswith('file:'):
            block = filesystems.LocalFileSystem(
                # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
                basepath=f'{infractl.fs.strip_file_scheme(base_path)}/{block_name}/',
            )
            return PrefectBlock(kind='local-file-system', name=block_name, block=block)
        else:
            block = filesystems.RemoteFileSystem(
                # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
                basepath=f'{base_path}/{block_name}/',
                settings=self.remote_storage_settings,
            )
            return PrefectBlock(kind='remote-file-system', name=block_name, block=block)

    async def create_code_block(self, block_name: str) -> PrefectBlock:
        """Creates and saves Prefect storage block."""
        base_path = self.settings('prefect_storage_basepath', 's3://prefect')
        block = self.define_storage_block(base_path, block_name)
        await block.save(overwrite=True, client=self.prefect_client)
        return block

    async def create_result_block(self, block_name: str) -> PrefectBlock:
        """Creates and saves Prefect result storage block."""
        storage_path = self.settings('prefect_storage_basepath', 's3://prefect')
        block = self.define_storage_block(f'{storage_path}/_persistent_results', block_name)
        await block.save(overwrite=True, client=self.prefect_client)
        return block

    async def create_files_block(self, block_name: str) -> PrefectBlock:
        """Creates a Prefect storage block, uploads runtime files and the extraction script."""
        identity = infractl.identity.generate()
        storage_path = self.settings('prefect_storage_basepath', 's3://prefect')
        base_path = f'{storage_path}/_files/{identity}'
        block = self.define_storage_block(base_path, f'{identity}-{block_name}-files')
        await block.save(overwrite=True, client=self.prefect_client)
        await self.upload_files(block)
        return block

    async def upload_files(self, block: PrefectBlock):
        """Uploads files to a files block."""
        # Use a unique file name to make sure it does not overlap with user's files.
        # The script extracts the runtime files to the directory specified as the first argument
        # (the current directory by default). "$SCRIPT_PATH" points to the directory with this
        # script and all required files.
        self._script = '81503f92-f80a-4a8f-855c-b399f2ec41df.sh'
        script_lines = [
            '#!/bin/bash',
            'set -e',
            'SCRIPT_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )',
            'TARGET_PATH="${1:-.}"',
            'if [[ -f "$SCRIPT_PATH/cwd.tar" ]]; then tar xvf "$SCRIPT_PATH/cwd.tar" -C "$TARGET_PATH"; fi',
        ]
        # Create a temporary directory with the required files, generate bash script to extract the
        # files to the corresponding locations in runtime, upload the whole directory content to the
        # file storage.
        with tempfile.TemporaryDirectory() as dirname:
            target_path = pathlib.Path(dirname)
            script_path = target_path / self._script
            infractl.fs.prepare_to_upload(self.runtime.files, target_path)
            script_path.write_text('\n'.join(script_lines))
            await block.block.put_directory(local_path=dirname)
        self._files_block = block.full_name

    def settings(self, name: str, default_value: Any = None) -> Any:
        """Return a setting value for this infrastructure address."""
        current_settings = self._settings or infractl.base.SETTINGS
        return current_settings.get(
            f'{self.infrastructure_implementation.address}.{name}', default_value
        )
