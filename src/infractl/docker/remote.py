"""Builds and pushes a Docker image to Docker registry using ICL cluster.

1. Upload the specified context recursively (with .dockerignore) to the cluster storage.
2. Create a Kubernetes Job that
    a. downloads the context to a temporary directory
    b. builds a Docker image
    c. pushes the Docker image to the container registry

The code needs to set the job TTL, so it will be deleted after completion.
"""
import copy
import logging
import re
import warnings
from typing import Any, Dict, Optional

import infractl
import infractl.base
import infractl.docker
import infractl.logging


class Builder(infractl.docker.Builder):
    """Builds and pushes a Docker image to Docker registry using ICL cluster."""

    logger: logging.Logger

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(
        self,
        stream_callback: Optional[infractl.docker.StreamCallback] = infractl.docker.stdout_callback,
        **kwargs,
    ) -> infractl.docker.Image:
        """Builds and pushes a Docker image to Docker registry using ICL cluster.

        Arguments:
        https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build
        """

        # TODO: move to the global import after fixing the issue with logger
        # pylint: disable=import-outside-toplevel, unused-import
        from prefect import futures

        # TODO: image full tag (name:tag) is currently required!
        for key in ('path', 'tag'):
            if key not in kwargs:
                raise ValueError(f'Argument {key} is required')

        path = kwargs['path']
        if not path.endswith('/'):
            path = f'{path}/'

        build_args = kwargs.copy()
        build_args['path'] = path

        with warnings.catch_warnings():
            # Disabling warning in JupyterLub:
            # UserWarning: `sync` called from an asynchronous context; you should `await` the async
            # function directly instead.
            warnings.simplefilter('ignore', category=UserWarning)
            futures.sync(self._async_build, **build_args)

        return infractl.docker.Image.from_full_name(kwargs['tag'])

    async def _async_build(self, **build_args):
        """Deploys and runs Prefect builder."""
        self.logger = infractl.logging.get_logger(__name__)

        # pylint: disable=import-outside-toplevel, unused-import
        from infractl.docker.prefect import builder

        runtime = infractl.runtime(
            # TODO: consider using a custom image for faster start
            dependencies={
                'pip': ['psutil'],
            },
            files=[
                {'src': build_args['path'], 'dst': 'context/'},
            ],
        )

        self.logger.info('Deploying Prefect builder flow')
        program = await infractl.deploy(
            infractl.program(builder.build),
            runtime=runtime,
            infrastructure=self.infrastructure.infrastructure,
            manifest_filter=self.manifest_filter,
        )

        self.logger.info('Running Prefect builder flow')
        flow_run = await program.run(
            parameters={
                'build_args': build_args,
                'registry': self.registry_internal_endpoint,
            },
            detach=True,
        )

        self.logger.info('Prefect flow run: %s', flow_run)
        await flow_run.stream_logs()
        if not flow_run.is_completed():
            raise infractl.docker.BuilderError(f'Remote build failed in {flow_run}')

    def manifest_filter(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Filters Kubernetes Job manifest."""
        # TODO: use registry mirror
        registry_mirror = None
        insecure_registries = [re.sub(r'^https?://', '', self.registry_internal_endpoint)]

        args = []
        if registry_mirror:
            args.extend(['--registry-mirror', registry_mirror])
        if insecure_registries:
            for registry in insecure_registries:
                args.extend(['--insecure-registry', registry])

        manifest = copy.deepcopy(manifest)

        job = manifest['spec']
        pod = job['template']['spec']
        prefect_container = pod['containers'][0]

        # pod volumes
        volumes = pod.setdefault('volumes', [])
        volumes.append({'name': 'certs-client', 'emptyDir': {}})

        # dind container
        pod['containers'].append(
            {
                'name': 'dind',
                'image': 'docker:dind',
                'imagePullPolicy': 'IfNotPresent',
                'env': [
                    {'name': 'DOCKER_TLS_CERTDIR', 'value': '/certs'},
                ],
                'args': args,
                'volumeMounts': [
                    {'name': 'certs-client', 'mountPath': '/certs/client'},
                ],
                'securityContext': {
                    'privileged': True,
                },
            },
        )

        # set TTL for the job to be automatically removed after 10 minutes
        job['ttlSecondsAfterFinished'] = 600

        # run dind and prefect in the same process namespace, so prefect can see dind process and
        # terminate it when necessary
        pod['shareProcessNamespace'] = True

        # set environment variables in prefect-job container
        prefect_env = prefect_container.setdefault('env', {})
        prefect_env.append({'name': 'DOCKER_HOST', 'value': 'tcp://localhost:2376'})
        prefect_env.append({'name': 'DOCKER_TLS_VERIFY', 'value': '1'})
        prefect_env.append({'name': 'DOCKER_CERT_PATH', 'value': '/certs/client'})

        # attach docker certs to prefect container
        volume_mounts = prefect_container.setdefault('volumeMounts', [])
        volume_mounts.append({'name': 'certs-client', 'mountPath': '/certs/client'})

        # run prefect container as privileged to allow killing docker process
        prefect_container['securityContext'] = {'privileged': True}

        return manifest
