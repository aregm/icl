"""ICL Kubernetes runtime implementation."""

from __future__ import annotations

import base64
import pathlib
import random
import string
from typing import Any, Dict, List, Optional, Union

import s3fs
from kubernetes import client, watch

import infractl.base
from infractl import identity, kubernetes

KubernetesManifest = infractl.base.KubernetesManifest


class KubernetesRuntimeSettings:
    """Kubernetes runtime settings."""

    namespace: str = 'default'
    image: str = 'python:3.9-slim'
    s3_base_path: str = 'prefect/infractl/kubernetes'
    working_dir = '/root'


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
        remote_path = f'{self.settings.s3_base_path}/{name}'

        fs_spec = {
            'key': 'x1miniouser',
            'secret': 'x1miniopass',
            'use_ssl': False,
            'client_kwargs': {
                'endpoint_url': 'http://s3.localtest.me',
            },
        }
        remote_fs = s3fs.S3FileSystem(**fs_spec)
        remote_fs.put(str(program_path), f'{remote_path}/')

        secret = _get_secret(name, _get_s3cmd_config())
        kubernetes.api().recreate_secret(namespace=self.settings.namespace, body=secret)

        job = _get_job(name)
        job.spec.template.spec.containers[0].image = self.settings.image
        job.spec.template.spec.volumes = [
            client.V1Volume(name='s3cfg', secret=client.V1SecretVolumeSource(secret_name=name))
        ]
        job.spec.template.spec.containers[0].volume_mounts = [
            client.V1VolumeMount(name='s3cfg', read_only=True, mount_path='/secrets')
        ]
        job.spec.template.spec.containers[0].working_dir = self.settings.working_dir
        command_lines = [
            'pip install s3cmd',
            f's3cmd --config=/secrets/.s3cfg get --recursive s3://{remote_path}/ .',
            'pwd',
            'ls -l',
            f'python {program_path.name}',
        ]
        job.spec.template.spec.containers[0].command = [
            '/bin/bash',
            '-xc',
            '\n'.join(command_lines),
        ]
        # TODO: use activeDeadlineSeconds for the timeout

        kubernetes.api().recreate_job(namespace=self.settings.namespace, body=job)
        return infractl.base.DeployedProgram(
            program=program,
            runner=KubernetesRunner(name, self.settings.namespace),
        )


class KubernetesRunner(infractl.base.Runnable):
    """Kubernetes runner."""

    name: str
    namespace: str

    def __init__(self, name: str, namespace: str):
        self.name = name
        self.namespace = namespace

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
        for event in watch.Watch().stream(
            func=kubernetes.api().core_v1().list_namespaced_pod,
            namespace=self.namespace,
            timeout_seconds=timeout,
            label_selector=f'job-name={self.name}',
        ):
            if event['object'].status.phase == 'Succeeded':
                return KubernetesProgramRun(completed=True)
            elif event['object'].status.phase == 'Failed':
                return KubernetesProgramRun(completed=False)
            elif event['object'].status.phase == 'Running':
                continue
            # deleted while watching for it
            if event['type'] == 'DELETED':
                return KubernetesProgramRun(completed=False, message='Cancelled')
        # TODO: stop job if it is still running
        return KubernetesProgramRun(completed=False, message='Timed out')


class KubernetesProgramRun(infractl.base.ProgramRun):
    """Kubernetes program run."""

    completed: bool
    message: Optional[str]

    def __init__(self, completed: bool = True, message: Optional[str] = None):
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


def _get_job(name: str) -> client.V1Job:
    """Returns Kubernetes Job."""
    return client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=client.V1ObjectMeta(name=name),
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
            backoff_limit=1,
            completion_mode='NonIndexed',
            completions=1,
            parallelism=1,
            ttl_seconds_after_finished=600,
        ),
    )
