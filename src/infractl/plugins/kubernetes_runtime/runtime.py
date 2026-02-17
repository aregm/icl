"""ICL Kubernetes runtime implementation.

TODO:
* deployment timeout
* run timeout
* cancel (required for integration test)
"""

from __future__ import annotations

import base64
import enum
import functools
import pathlib
import random
import string
import sys
import tempfile
from typing import Any, Dict, List, Optional, Union

import fsspec
import s3fs
from kubernetes import client, watch

import infractl.base
import infractl.fs
from infractl import defaults, identity, kubernetes
from infractl.plugins.kubernetes_runtime import engine
from infractl.plugins.kubernetes_runtime.program import load

KubernetesManifest = infractl.base.KubernetesManifest


class KubernetesRuntimeError(Exception):
    """Kubernetes runtime error."""


class KubernetesRuntimeSettings:
    """Kubernetes runtime settings."""

    namespace: str = 'default'

    image: str = defaults.PREFECT_IMAGE

    s3_base_path: str = 'prefect/infractl/kubernetes'

    working_dir = '/root'

    dependencies = ['s3cmd', 'pydantic']
    """Required dependencies to install before downloading program."""

    address = 'localtest.me'

    @property
    def s3_url(self):
        """S3 endpoint."""
        return f'http://s3.{self.address}'

    @property
    def prefect_api_url(self):
        """Prefect endpoint."""
        return f'http://prefect.{self.address}/api'

    @property
    def remote_fs_spec(self):
        """Remote fs spec."""
        return {
            'key': 'x1miniouser',
            'secret': 'x1miniopass',  # nosec B105 - development default
            'use_ssl': False,
            'client_kwargs': {
                'endpoint_url': self.s3_url,
            },
        }


class RemoteStorage:
    """Remote storage."""

    fs: fsspec.AbstractFileSystem
    base_path: str

    def __init__(self, fs: fsspec.AbstractFileSystem, base_path: str):
        self.fs = fs
        self.base_path = base_path


class KubernetesRuntimeImplementation(
    infractl.base.RuntimeImplementation, registration_name='kubernetes'
):
    """Kubernetes runtime implementation."""

    settings = KubernetesRuntimeSettings()

    async def deploy(
        self,
        program: infractl.base.program.Program,
        name: Optional[str] = None,
        **kwargs,
    ) -> infractl.base.DeployedProgram:
        """Deploys a program."""

        program = load(program)

        program_path = pathlib.Path(program.path)
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        if name:
            name = identity.sanitize(name)
        else:
            name = identity.generate(suffix=f'{program_path.stem}-{random_part}')

        base_path = f'{self.settings.s3_base_path}/{name}'
        remote_fs = s3fs.S3FileSystem(**self.settings.remote_fs_spec)

        code_path = f'{base_path}/code'
        data_path = f'{base_path}/data'

        # upload the program
        remote_fs.put(str(program_path), f'{code_path}/')

        # upload runtime files
        if self.runtime.files:
            with tempfile.TemporaryDirectory() as dirname:
                target_path = pathlib.Path(dirname)
                infractl.fs.prepare_to_upload(self.runtime.files, target_path)
                remote_fs.put(lpath=f'{dirname}/', rpath=f'{data_path}/', recursive=True)

        # upload engine
        remote_fs.put(lpath=engine.__file__, rpath=f'{data_path}/')

        # upload dependencies
        if self.runtime.dependencies.pip:
            with tempfile.NamedTemporaryFile(delete=False) as requirements_file:
                requirements_file.write('\n'.join(self.runtime.dependencies.pip).encode('utf-8'))
                requirements_file.flush()
                requirements_file.close()
                remote_fs.put(lpath=requirements_file.name, rpath=f'{data_path}/requirements.txt')

        secret = _get_secret(name, _get_s3cmd_config())
        kubernetes.api().recreate_secret(namespace=self.settings.namespace, body=secret)

        job = _get_job(name, self.settings.namespace)
        job.spec.template.spec.containers[0].image = self.settings.image
        job.spec.template.spec.volumes = [
            client.V1Volume(name='s3cfg', secret=client.V1SecretVolumeSource(secret_name=name))
        ]
        job.spec.template.spec.containers[0].volume_mounts = [
            client.V1VolumeMount(name='s3cfg', read_only=True, mount_path='/secrets')
        ]
        job.spec.template.spec.containers[0].working_dir = self.settings.working_dir

        s3cmd_get = 's3cmd --config=/secrets/.s3cfg get --recursive --force'
        s3cmd_put = 's3cmd --config=/secrets/.s3cfg put --force'
        engine_cmd = f'python $__ICL_DATA_DIR/engine.py {program_path.name}'
        if program.name:
            engine_cmd += f' --entrypoint {program.name}'
        elif program.flow:
            engine_cmd += f' --flow {program.flow}'

        command_lines = []
        if self.settings.dependencies:
            command_lines = [f'pip install {" ".join(self.settings.dependencies)}']

        command_lines += [
            '__ICL_DATA_DIR=$(mktemp -d)',
            'pip install s3cmd pydantic',
            f'{s3cmd_get} s3://{code_path}/ .',
            f'{s3cmd_get} s3://{data_path}/ $__ICL_DATA_DIR/',
            'if [[ -f "$__ICL_DATA_DIR/requirements.txt" ]]; then',
            '  pip install -r "$__ICL_DATA_DIR/requirements.txt"',
            'fi',
            'if [[ -f "$__ICL_DATA_DIR/cwd.tar" ]]; then tar xvf "$__ICL_DATA_DIR/cwd.tar"; fi',
            'pwd',
            'ls -l . $__ICL_DATA_DIR',
            'export PYTHONPATH=$PWD',
            engine_cmd,
            'if [[ -f "$__ICL_DATA_DIR/result.json" ]]; then',
            f'  {s3cmd_put} "$__ICL_DATA_DIR/result.json" s3://{data_path}/',
            'fi',
        ]
        job.spec.template.spec.containers[0].command = [
            '/bin/bash',
            '-xec',
            '\n'.join(command_lines),
        ]

        env = self.runtime.environment.copy()

        if program.flow:
            env['PREFECT_API_URL'] = self.settings.prefect_api_url

        if env:
            job.spec.template.spec.containers[0].env = [
                client.V1EnvVar(name=key, value=value) for key, value in env.items()
            ]

        # TODO: use activeDeadlineSeconds for the timeout

        return infractl.base.DeployedProgram(
            program=program,
            runner=KubernetesRunner(job, RemoteStorage(fs=remote_fs, base_path=base_path)),
        )


class ProgramState(enum.Enum):
    UNKNOWN = enum.auto()
    SCHEDULED = enum.auto()
    RUNNING = enum.auto()
    COMPLETED = enum.auto()
    FAILED = enum.auto()

    def capitalize(self) -> str:
        """Returns a capitalized state, for example "Completed"."""
        return self.name.lower().capitalize()


class KubernetesRunner(infractl.base.Runnable):
    """Kubernetes runner."""

    manifest: client.V1Job
    storage: RemoteStorage
    state: ProgramState

    def __init__(self, manifest: client.V1Job, storage: RemoteStorage):
        self.manifest = manifest
        self.storage = storage
        self.state = ProgramState.UNKNOWN

    @property
    def name(self):
        """Return Job name."""
        return self.manifest.metadata.name

    @property
    def namespace(self):
        """Return Job namespace."""
        return self.manifest.metadata.namespace

    @property
    def data_path(self):
        """Returns data path."""
        return f'{self.storage.base_path}/data'

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> infractl.base.ProgramRun:
        """Runs this runnable.

        Args:
            parameters: a dictionary of named arguments if a program's entry point is a function,
                a list of arguments otherwise.
            timeout: timeout in seconds to wait for a program completion, `None` (default) to wait
                forever.
            detach: `False` (default) to wait for a program completion, `True` to start the program
                and detach from it.
        """

        # upload parameters
        if parameters:
            with tempfile.NamedTemporaryFile(delete=False) as requirements_file:
                requirements_file.write(engine.dumps(parameters))
                requirements_file.flush()
                requirements_file.close()
                self.storage.fs.put(
                    lpath=requirements_file.name,
                    rpath=f'{self.data_path}/parameters.json',
                )

        kubernetes.api().recreate_job(namespace=self.namespace, body=self.manifest)
        self.state = ProgramState.SCHEDULED

        program_run = KubernetesProgramRun(self, timeout=timeout)
        if not detach:
            await program_run.wait()
        return program_run


class KubernetesProgramRun(infractl.base.ProgramRun):
    """Kubernetes program run."""

    runner: KubernetesRunner
    timeout: Optional[float] = None

    def __init__(self, runner: KubernetesRunner, timeout: Optional[float] = None):
        self.runner = runner
        self.timeout = timeout

    def is_scheduled(self) -> bool:
        return self.runner.state == ProgramState.SCHEDULED

    def is_pending(self) -> bool:
        return False

    def is_running(self) -> bool:
        return self.runner.state == ProgramState.RUNNING

    def is_completed(self) -> bool:
        return self.runner.state == ProgramState.COMPLETED

    def is_failed(self) -> bool:
        return self.runner.state == ProgramState.FAILED

    def is_crashed(self) -> bool:
        return False

    def is_cancelling(self) -> bool:
        return False

    def is_cancelled(self) -> bool:
        return False

    def is_final(self) -> bool:
        return self.runner.state in (ProgramState.COMPLETED, ProgramState.FAILED)

    def is_paused(self) -> bool:
        return False

    @functools.cached_property
    def pod_name(self) -> str:
        """Returns program pod name"""
        pod_list: client.V1PodList = (
            kubernetes.api()
            .core_v1()
            .list_namespaced_pod(
                namespace=self.runner.namespace,
                label_selector=f'job-name={self.runner.name}',
            )
        )
        if len(pod_list.items) > 1:
            raise KubernetesRuntimeError(f'Multiple pods for job {self.runner.name}')
        if len(pod_list.items) < 1:
            raise KubernetesRuntimeError(f'Pod not found for job {self.runner.name}')
        return pod_list.items[0].metadata.name

    async def wait(self, wait_for: Optional[ProgramState] = None) -> None:
        for event in watch.Watch().stream(
            func=kubernetes.api().core_v1().list_namespaced_pod,
            namespace=self.runner.namespace,
            timeout_seconds=3600,
            label_selector=f'job-name={self.runner.name}',
        ):
            if event['object'].status.phase == 'Succeeded':
                self.runner.state = ProgramState.COMPLETED
                return
            elif event['object'].status.phase == 'Failed':
                self.runner.state = ProgramState.FAILED
                return
            elif event['object'].status.phase == 'Running':
                self.runner.state = ProgramState.RUNNING
                if self.runner.state == wait_for:
                    return
            # deleted while watching for it
            if event['type'] == 'DELETED':
                self.runner.state = ProgramState.FAILED
                return

        # timed out
        # TODO: timed out, stop job if it is still running

    async def result(self) -> Any:
        """Returns program result."""
        result_remote_path = f'{self.runner.data_path}/result.json'
        if not self.runner.storage.fs.exists(result_remote_path):
            return None
        with tempfile.TemporaryDirectory() as dirname:
            result_path = pathlib.Path(dirname) / 'results.json'
            self.runner.storage.fs.get(rpath=result_remote_path, lpath=str(result_path))
            with result_path.open('rb') as result_file:
                return engine.loads(result_file.read())

    async def logs(self) -> List[str]:
        """Returns program logs."""
        return (
            kubernetes.api()
            .core_v1()
            .read_namespaced_pod_log(
                name=self.pod_name,
                namespace=self.runner.namespace,
                container='program',
            )
            .splitlines()
        )

    async def stream_logs(self, file=None) -> None:
        """Stream logs until the terminal state is reached.

        Args:
            file:  a file-like object (stream); defaults to the current sys.stdout.
        """
        await self.wait(wait_for=ProgramState.RUNNING)
        if not self.is_running():
            return
        file = file or sys.stdout
        for line in watch.Watch().stream(
            kubernetes.api().core_v1().read_namespaced_pod_log,
            name=self.pod_name,
            namespace=self.runner.namespace,
            container='program',
        ):
            print(line, file=file)
        await self.wait()

    def __repr__(self) -> str:
        """Returns a string representation.

        Note that JupyterLab uses __repr__ instead of __str__.
        """
        return f'{self.runner.name} ({self.runner.state.capitalize()})'


def _get_secret(name: str, data: str) -> client.V1Secret:
    """Returns Kubernetes Secret."""
    return client.V1Secret(
        api_version='v1',
        kind='Secret',
        metadata=client.V1ObjectMeta(name=name),
        data={
            '.s3cfg': base64.b64encode(data.encode('utf-8')).decode('utf-8'),
        },
    )


def _get_s3cmd_config() -> str:
    return '\n'.join(
        [
            '[default]',
            'access_key = x1miniouser',
            'secret_key = x1miniopass',
            'signature_v2 = False',
            'use_https = True',
            'check_ssl_certificate = False',
            'host_base = minio.minio',
            'host_bucket = minio.minio',
        ]
    )


def _get_job(name: str, namespace: str) -> client.V1Job:
    """Returns Kubernetes Job."""
    return client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1JobSpec(
            template=client.V1JobTemplateSpec(
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name='program',
                            image_pull_policy='IfNotPresent',
                        ),
                    ],
                    restart_policy='Never',
                )
            ),
            backoff_limit=0,
            completion_mode='NonIndexed',
            completions=1,
            parallelism=1,
            ttl_seconds_after_finished=600,
        ),
    )
