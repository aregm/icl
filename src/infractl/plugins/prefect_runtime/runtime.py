"""ICL Prefect runtime implementation.

Environment variable PREFECT_API_URL needs to be set to the URL of a Prefect server running in the
cluster.

"""

import asyncio
import contextlib
import copy
import functools
import os
import pathlib
import sys
import tarfile
import tempfile
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Union

import dynaconf
import prefect.blocks.core as blocks
import pydantic
from prefect import deployments, filesystems, infrastructure, settings
from prefect.client import orchestration
from prefect.server.api import server

import infractl
import infractl.base
import infractl.plugins.prefect_runtime.utils as prefect_utils
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
]


ManifestFilter = Callable[[infrastructure.KubernetesManifest], infrastructure.KubernetesManifest]
"""Accepts Kubernetes manifest as a dictionary and returns an updated manifest."""


class PrefectRuntimeError(Exception):
    """Prefect runtime error."""


def strip_file_scheme(uri: str) -> str:
    """Strips "file" schema from the URI.

    Examples:
        file:///C:/Windows -> C:/Windows
        file:///home -> /home
        file:local -> local
    """
    path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
    if sys.platform == 'win32' and path.startswith('/'):
        # workaround to remove leading slash on Windows
        return path[1:]
    return path


def stable_identity() -> str:
    """Generates stable identity for the current user.

    Uses environment variables `JUPYTERHUB_USER`, `USER` and sanitizes the value to make it
    compatible with Prefect names.
    """
    identity = os.environ.get('JUPYTERHUB_USER') or os.environ.get('USER') or 'unknown'
    return prefect_runtime.sanitize(identity)


def upload_files(files: List[infractl.base.RuntimeFile], target_path: pathlib.Path):
    """Uploads files to the specified directory."""
    # The specified directory has the following structure:
    # cwd.tar  - tarball to extract to the current directory in runtime.
    with tarfile.open(name=target_path / 'cwd.tar', mode='w') as cwd:
        for file in files:
            if file.src.endswith('/'):
                src = pathlib.Path(file.src)
                dst = ''
                if file.dst:
                    # dst is expected to be a directory, adding a trailing / if missing
                    dst = file.dst if file.dst.endswith('/') else f'{file.dst}/'
                for path in src.rglob('*'):
                    relative_path = path.relative_to(src)
                    cwd.add(name=path, arcname=f'{dst}{relative_path}')
            else:
                dst = file.dst or file.src
                cwd.add(name=file.src, arcname=pathlib.Path(dst).name)


class PrefectBlock(pydantic.BaseModel):
    """Prefect Block specification."""

    kind: str
    name: str
    block: Optional[blocks.Block] = None

    @property
    def full_name(self):
        return f'{self.kind}/{self.name}'

    async def save(self, **kwargs):
        return await self.block.save(self.name, **kwargs)


class PrefectProgramRunner(infractl.base.Runnable):
    """Prefect program."""

    def __init__(
        self,
        prefect_client: orchestration.PrefectClient,
        prefect_deployment: deployments.Deployment,
    ):
        self.prefect_client = prefect_client
        self.prefect_deployment = prefect_deployment

    @property
    def deployment(self) -> deployments.Deployment:
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

        deployment_name = f'{self.prefect_deployment.flow_name}/{self.prefect_deployment.name}'
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
        program: prefect_runtime.PrefectProgram,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[ManifestFilter] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Deploys a program."""
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
        manifest_filter: Optional[ManifestFilter] = None,
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
        manifest_filter: Optional[ManifestFilter] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> infractl.base.DeployedProgram:
        """Deploys a Prefect program."""
        if not isinstance(program, prefect_runtime.PrefectProgram):
            raise NotImplementedError(f'PrefectProgram expected, got {program.__class__.__name__}')

        flow_file_name = pathlib.Path(program.path).name
        prefect_flow = program.flow
        # use a custom flow name if specified
        if name:
            # create a copy of the flow object with a new name to make sure to keep to original
            # object intact for the case it was imported as Python object.
            prefect_flow = prefect_flow.with_options(name=name)

        prefect_storage_block = await self.create_code_block(prefect_flow.name)
        if self.runtime.files:
            await self.create_files_block(prefect_flow.name)
        prefect_infrastructure_block = await self.create_infrastructure_block(
            prefect_flow.name,
            customizations=customizations,
            manifest_filter=manifest_filter,
        )

        prefect_flow_entrypoint = f'{flow_file_name}:{prefect_flow.fn.__name__}'
        prefect_deployment = await deployments.Deployment.build_from_flow(
            flow=prefect_flow,
            # Note that Prefect shows deployments as "{flow_name}/{deployment_name}".
            name=program.deployment_name,
            storage=await blocks.Block.load(
                prefect_storage_block.full_name,
                client=self.prefect_client,
            ),
            infrastructure=await blocks.Block.load(
                prefect_infrastructure_block.full_name,
                client=self.prefect_client,
            ),
            work_queue_name=self.settings('prefect_queue', 'prod'),
            apply=False,
            skip_upload=True,
            entrypoint=prefect_flow_entrypoint,
        )

        deployment_keys = prefect_deployment.dict().keys()
        deployment_dict = {}
        for key, value in kwargs.items():
            if key in deployment_keys:
                deployment_dict[key] = value
        if deployment_dict:
            await prefect_deployment.update(**deployment_dict)

        cwd = os.getcwd()
        os.chdir(pathlib.Path(program.path).absolute().parent)
        ignore_file_name: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as ignore_file:
                ignore_file_name = ignore_file.name
                ignore_file.write('\n'.join(DEFAULT_ITEMS_TO_IGNORE).encode('utf-8'))
                ignore_file.flush()
                ignore_file.close()
                await prefect_deployment.upload_to_storage(
                    prefect_storage_block.full_name,
                    ignore_file=ignore_file_name,
                )
        finally:
            os.chdir(cwd)
            if ignore_file_name:
                with contextlib.suppress(FileNotFoundError):
                    os.remove(ignore_file_name)

        await prefect_deployment.apply(upload=False)

        return infractl.base.DeployedProgram(
            program=program,
            runner=PrefectProgramRunner(self.prefect_client, prefect_deployment),
        )

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
            client_kwargs[
                'endpoint_url'
            ] = f'http://s3.{self.infrastructure_implementation.address}'
        return storage_settings

    def define_storage_block(self, base_path: str, name: str) -> PrefectBlock:
        """Defines Prefect storage block.

        The following Prefect storage blocks are supported:
        * LocalFileSystem (scheme is "file")
        * RemoteFileSystem (scheme is not "file")
        """
        if base_path.startswith('file:'):
            block = filesystems.LocalFileSystem(
                # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
                basepath=f'{strip_file_scheme(base_path)}/{name}/',
            )
            return PrefectBlock(kind='local-file-system', name=name, block=block)
        else:
            block = filesystems.RemoteFileSystem(
                # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
                basepath=f'{base_path}/{name}/',
                settings=self.remote_storage_settings,
            )
            return PrefectBlock(kind='remote-file-system', name=name, block=block)

    async def create_code_block(self, flow_name: str) -> PrefectBlock:
        """Creates and saves Prefect storage block."""
        base_path = self.settings('prefect_storage_basepath', 's3://prefect')
        block = self.define_storage_block(base_path, flow_name)
        await block.save(overwrite=True, client=self.prefect_client)
        return block

    async def create_files_block(self, flow_name: str):
        """Creates a Prefect storage block, upload files and script for infractl.prefect.engine."""
        identity = stable_identity()
        storage_path = self.settings('prefect_storage_basepath', 's3://prefect')
        base_path = f'{storage_path}/_files/{identity}'
        block = self.define_storage_block(base_path, f'{identity}-{flow_name}-files')
        await block.save(overwrite=True, client=self.prefect_client)
        await self.upload_files(block)

    async def upload_files(self, block: PrefectBlock):
        """Uploads files to a files block."""
        # Use a unique file name to make sure it does not overlap with user's files.
        # This script is located in the temporary directory in runtime, but executed from the
        # current directory in runtime. So "$PWD" (or ".") points to the current directory,
        # "$SCRIPT_PATH" points to the temporary directory with this script and all required files.
        self._script = '81503f92-f80a-4a8f-855c-b399f2ec41df.sh'
        script_lines = [
            '#!/bin/bash',
            'set -e',
            'SCRIPT_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )',
            'if [[ -f "$SCRIPT_PATH/cwd.tar" ]]; then tar xvf "$SCRIPT_PATH/cwd.tar"; fi',
        ]
        # Create a temporary directory with the required files, generate bash script to extract the
        # files to the corresponding locations in runtime, upload the whole directory content to the
        # file storage.
        with tempfile.TemporaryDirectory() as dirname:
            target_path = pathlib.Path(dirname)
            script_path = target_path / self._script
            upload_files(self.runtime.files, target_path)
            script_path.write_text('\n'.join(script_lines))
            await block.block.put_directory(local_path=dirname)
        self._files_block = block.full_name

    async def create_infrastructure_block(
        self,
        flow_name: str,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[ManifestFilter] = None,
    ) -> PrefectBlock:
        """Creates Prefect infrastructure block."""
        block = self.kubernetes_job(customizations=customizations, manifest_filter=manifest_filter)
        await block.save(flow_name, overwrite=True, client=self.prefect_client)
        return PrefectBlock(kind='kubernetes-job', name=flow_name)

    def kubernetes_job(
        self,
        customizations: Optional[List[Dict[str, Any]]] = None,
        manifest_filter: Optional[ManifestFilter] = None,
    ) -> infrastructure.KubernetesJob:
        """Creates Prefect KubernetesJob block."""
        job_args = {
            'customizations': customizations.copy() if customizations else [],
            'env': self.runtime.environment.copy() if self.runtime.environment else {},
        }

        # TODO: move the default image to discover
        image = self.settings('prefect_image', 'pbchekin/x1-prefect:2.13.0-python3.9-20231010')
        if image:
            job_args['image'] = image

        # TODO: support different targets runtime dependencies, such as using a custom docker image
        if self.runtime.dependencies.pip:
            # TODO: check if environment variable EXTRA_PIP_PACKAGES is set and merge if necessary
            job_args['env']['EXTRA_PIP_PACKAGES'] = ' '.join(self.runtime.dependencies.pip)

        # TODO: support different file injection methods, such as using a custom docker image
        if self.runtime.files:
            job_args['command'] = [
                'python',
                '-m',
                'x1.prefect.engine',
                '--block',
                self._files_block,
                '--script',
                self._script,
            ]

        # name is required for `build_job`
        job = infrastructure.KubernetesJob(name='foo', **job_args)
        manifest = job.build_job()

        manifest = self.manifest_filter(manifest)
        if manifest_filter:
            manifest = manifest_filter(manifest)

        metadata = manifest['metadata']
        metadata.pop('namespace', None)
        metadata.pop('generateName', None)

        # The following parameters are applied already in manifest, do not set them again
        job_args.pop('customizations', None)
        job_args.pop('env')

        return infrastructure.KubernetesJob(job=manifest, **job_args)

    def manifest_filter(
        self,
        manifest: infrastructure.KubernetesManifest,
    ) -> infrastructure.KubernetesManifest:
        """Filters Kubernetes Job manifest.

        Adds shared volume, if enabled.
        Adds GPU resource, if enabled
        """
        manifest = copy.deepcopy(manifest)
        prefect_pod = manifest['spec']['template']['spec']
        prefect_container = prefect_pod['containers'][0]

        # TODO: make it customizable, also use discover
        shared_volume_mount = self.settings('prefect_shared_volume_mount')
        if shared_volume_mount:
            volumes = prefect_pod.setdefault('volumes', [])
            volumes.append(
                {
                    'name': 'shared-volume',
                    'persistentVolumeClaim': {
                        'claimName': 'shared-volume',
                    },
                },
            )
            volume_mounts = prefect_container.setdefault('volumeMounts', [])
            volume_mounts.append(
                {
                    'name': 'shared-volume',
                    'mountPath': shared_volume_mount,
                },
            )

        gpus = self.infrastructure_implementation.gpus
        if gpus:
            resources = prefect_container.setdefault('resources', {})
            limits = resources.setdefault('limits', {})
            limits[gpus[0]] = str(gpus[1])

        return manifest

    def settings(self, name: str, default_value: Any = None) -> Any:
        """Return a setting value for this infrastructure address."""
        current_settings = self._settings or infractl.base.SETTINGS
        return current_settings.get(
            f'{self.infrastructure_implementation.address}.{name}', default_value
        )
