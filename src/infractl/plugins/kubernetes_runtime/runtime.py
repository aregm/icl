"""ICL Kubernetes runtime implementation."""

from __future__ import annotations

import base64
import pathlib
import random
import string
import tempfile
from typing import Any, Dict, List, Optional, Union

import fsspec
import s3fs
from kubernetes import client, watch

import infractl.base
import infractl.fs
from infractl import identity, kubernetes
from infractl.plugins.kubernetes_runtime import engine

KubernetesManifest = infractl.base.KubernetesManifest


class KubernetesRuntimeSettings:
    """Kubernetes runtime settings."""

    namespace: str = 'default'
    image: str = 'python:3.9-slim'
    s3_base_path: str = 'prefect/infractl/kubernetes'
    working_dir = '/root'


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

        program_path = pathlib.Path(program.path)
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        name = name or identity.generate(suffix=f'{program_path.stem}-{random_part}')

        base_path = f'{self.settings.s3_base_path}/{name}'
        # TODO: make configurable
        fs_spec = {
            'key': 'x1miniouser',
            'secret': 'x1miniopass',
            'use_ssl': False,
            'client_kwargs': {
                'endpoint_url': 'http://s3.localtest.me',
            },
        }
        remote_fs = s3fs.S3FileSystem(**fs_spec)

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
        engine_cmd = f'python $__ICL_DATA_DIR/engine.py {program_path.name}'
        if program.name:
            engine_cmd += f' --entrypoint {program.name}'
        command_lines = [
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
        ]
        job.spec.template.spec.containers[0].command = [
            '/bin/bash',
            '-xc',
            '\n'.join(command_lines),
        ]

        if self.runtime.environment:
            job.spec.template.spec.containers[0].env = [
                client.V1EnvVar(name=key, value=value)
                for key, value in self.runtime.environment.items()
            ]

        # TODO: use activeDeadlineSeconds for the timeout

        return infractl.base.DeployedProgram(
            program=program,
            runner=KubernetesRunner(job, RemoteStorage(fs=remote_fs, base_path=base_path)),
        )


class KubernetesRunner(infractl.base.Runnable):
    """Kubernetes runner."""

    manifest: client.V1Job
    storage: RemoteStorage

    def __init__(self, manifest: client.V1Job, storage: RemoteStorage):
        self.manifest = manifest
        self.storage = storage

    @property
    def name(self):
        """Return Job name."""
        return self.manifest.metadata.name

    @property
    def namespace(self):
        """Return Job namespace."""
        return self.manifest.metadata.namespace

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
            data_path = f'{self.storage.base_path}/data'
            with tempfile.NamedTemporaryFile(delete=False) as requirements_file:
                requirements_file.write(engine.dumps(parameters))
                requirements_file.flush()
                requirements_file.close()
                self.storage.fs.put(
                    lpath=requirements_file.name,
                    rpath=f'{data_path}/parameters.json',
                )

        kubernetes.api().recreate_job(namespace=self.namespace, body=self.manifest)

        for event in watch.Watch().stream(
            func=kubernetes.api().core_v1().list_namespaced_pod,
            namespace=self.namespace,
            timeout_seconds=timeout,
            label_selector=f'job-name={self.name}',
        ):
            if event['object'].status.phase == 'Succeeded':
                return KubernetesProgramRun(name=self.name, completed=True)
            elif event['object'].status.phase == 'Failed':
                return KubernetesProgramRun(name=self.name, completed=False)
            elif event['object'].status.phase == 'Running':
                continue
            # deleted while watching for it
            if event['type'] == 'DELETED':
                return KubernetesProgramRun(name=self.name, completed=False, message='Cancelled')
        # TODO: stop job if it is still running
        return KubernetesProgramRun(name=self.name, completed=False, message='Timed out')


class KubernetesProgramRun(infractl.base.ProgramRun):
    """Kubernetes program run."""

    name: str
    completed: bool
    message: Optional[str]

    def __init__(self, name: str, completed: bool = True, message: Optional[str] = None):
        self.name = name
        self.completed = completed
        self.message = message

    def is_scheduled(self) -> bool:
        return True

    def is_pending(self) -> bool:
        return False

    def is_running(self) -> bool:
        return False

    def is_completed(self) -> bool:
        return self.completed

    def is_failed(self) -> bool:
        return not self.completed

    def is_crashed(self) -> bool:
        return False

    def is_cancelling(self) -> bool:
        return False

    def is_cancelled(self) -> bool:
        return False

    def is_final(self) -> bool:
        return True

    def is_paused(self) -> bool:
        return False

    async def wait(self, poll_interval=5) -> None:
        raise NotImplementedError()

    def __repr__(self) -> str:
        """Returns a string representation.

        Note that JupyterLab uses __repr__ instead of __str__.
        """
        status = 'Completed' if self.completed else 'Failed'
        return f'{self.name} ({status})'


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
