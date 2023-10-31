"""Builds and pushes a Docker image to Docker registry using a local Docker daemon."""
import itertools
import re
import tempfile
from typing import Optional

import docker.errors
import python_docker.base
import python_docker.registry

import infractl.docker
import infractl.logging

logger = infractl.logging.get_logger(__name__)


class Builder(infractl.docker.Builder):
    """Builds and pushes a Docker image to Docker registry using a local Docker daemon."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(
        self,
        stream_callback: Optional[infractl.docker.StreamCallback] = infractl.docker.stdout_callback,
        **kwargs,
    ) -> infractl.docker.Image:
        """Builds and pushes a Docker image to Docker registry using a local Docker daemon.

        Arguments:
        https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build
        """

        # TODO: image full tag (name:tag) is currently required!
        for key in ('path', 'tag'):
            if key not in kwargs:
                raise ValueError(f'Argument {key} is required')

        logger.info(
            'Building image %s from %s', kwargs.get('tag', '(untagged)'), kwargs.get('path', 'N/A')
        )

        client = docker.from_env()
        client_kwargs = kwargs.copy()
        # The returned stream will be decoded into dicts on the fly
        client_kwargs['decode'] = True
        # TODO: filter valid arguments for client.api.build
        resp = client.api.build(**client_kwargs)

        if isinstance(resp, str):
            return infractl.docker.Image.from_full_name(full_name=resp)

        last_event = None
        image_id = None
        result_stream, stream = itertools.tee(resp)
        for chunk in stream:
            if stream_callback and 'stream' in chunk:
                stream_callback(chunk['stream'].strip())
            if 'error' in chunk:
                raise docker.errors.BuildError(chunk['error'], result_stream)
            if not image_id and 'stream' in chunk:
                match = re.search(r'(^Successfully built |sha256:)([0-9a-f]+)$', chunk['stream'])
                if match:
                    image_id = match.group(2)
            last_event = chunk

        if image_id:
            image = infractl.docker.Image.from_full_name(id=image_id, full_name=kwargs.get('tag'))
            self.push(image)
            return image

        raise docker.errors.BuildError(last_event or 'Unknown', result_stream)

    def push(self, image: infractl.docker.Image):
        """Pushes the existing Docker image to registry."""
        image_id = image.full_name
        client = docker.from_env()
        docker_image = client.images.get(image_id)
        logger.info('Saving image %s', image_id)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tar_file_name = f'{tmp_dir}/{image_id}.tar'
            with open(tar_file_name, 'wb') as tar_file:
                for chunk in docker_image.save(named=True):
                    tar_file.write(chunk)

            pd_images = python_docker.base.Image.from_filename(tar_file_name)
            logger.info('Pushing image %s to %s', image_id, self.registry_endpoint)
            pd_registry = python_docker.registry.Registry(hostname=self.registry_endpoint)
            for pd_image in pd_images:
                pd_registry.push_image(pd_image)
