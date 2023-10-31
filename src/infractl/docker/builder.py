"""ICL Docker API.

This API allows building custom Docker images and pushing them to a Docker registry.

* It leverages the existing local Docker, if exists.
* If Docker cannot be used, it uses the existing ICL cluster to build an image.
* It can be used inside (for example, in JupyterLab) and outside an ICL cluster (for example, from
  user's laptop).
* It leverages the existing infrastructure to access ICL cluster and its resources.
* It supports direct K8s cluster API and ICL cluster API, when the former is not available.
"""

from __future__ import annotations

import enum
import os
import re
import shutil
from typing import Any, Callable, Optional, Union

import pydantic
import python_docker.registry
import requests.exceptions

import infractl.api
import infractl.api.infrastructure
import infractl.base

StreamCallback = Callable[[str], None]


def stdout_callback(line: str):
    """Stream callback that prints all messages to stdout."""
    print(line)


class BuilderError(Exception):
    """Base class for builder errors."""


class BuilderKind(enum.Enum):
    """Kind of Docker builder."""

    AUTO = 1
    """Auto detect which Docker builder to use (default)."""

    DOCKER = 2
    """Use local Docker daemon."""

    PREFECT = 3
    """Use Prefect installed in the provided infrastructure."""

    KUBERNETES = 4
    """Use Kubernetes cluster in the provided infrastructure."""

    @classmethod
    def list(cls):
        """Returns a list of possible kinds."""
        return list(map(lambda c: c.name, cls))


class Image(pydantic.BaseModel):
    """Docker image."""

    id: Optional[str] = None
    registry: Optional[str] = None
    name: Optional[str] = None
    tag: Optional[str] = None

    @classmethod
    # pylint: disable=redefined-builtin
    def from_full_name(cls, full_name: Optional[str] = None, id: Optional[str] = None):
        """Returns Image instance for a full name.

        Docker terminology for images is quite confusing: their "tag" means a "full" tag such as
        "ubuntu:22.04" and a "real" tag such as "22.04". This function accepts a full tag and
        optional id and returns an Image object.

        Examples:
        'ubuntu' -> name='ubuntu'
        'ubuntu:22.04' -> name='ubuntu', tag='22.04'
        'docker.io/ubuntu' -> registry='docker.io', name='ubuntu'
        'docker.io/ubuntu:22.04' -> registry='docker.io', name='ubuntu', tag='22.04'
        'localhost:5000/ubuntu' -> registry='localhost:5000', name='ubuntu'
        'localhost:5000/ubuntu:22.04' -> registry='localhost:5000', name='ubuntu', tag='22.04'
        """
        registry: Optional[str] = None
        name: Optional[str] = None
        tag: Optional[str] = None

        if full_name:
            parts = full_name.rsplit('/', 1)
            if len(parts) == 2:
                registry = parts[0]
                full_name = parts[1]

            parts = full_name.rsplit(':', 1)
            if len(parts) == 1:
                name = full_name
            elif len(parts) == 2:
                name = parts[0]
                tag = parts[1]

        return Image(id=id, registry=registry, name=name, tag=tag)

    @property
    def full_name(self):
        """Returns a full name for the image, or its id."""
        if not self.name:
            return self.id
        registry = f'{self.registry}/' if self.registry else ''
        tag = f':{self.tag}' if self.tag else ''
        return f'{registry}{self.name}{tag}'


class Builder:
    """Builds and pushes a Docker image to Docker registry."""

    infrastructure: infractl.base.InfrastructureImplementation
    registry: Optional[str] = None

    def __init__(
        self,
        infrastructure: Optional[infractl.base.Infrastructure] = None,
        registry: Optional[str] = None,
    ):
        """Docker builder.

        Args:
            infrastructure: ICL infrastructure, default one is used when not specified.
            registry: Docker registry, default one from infrastructure is used when not specified.
        """
        self.infrastructure = infractl.base.get_infrastructure_implementation(
            infrastructure or infractl.api.infrastructure.default_infrastructure()
        )
        self.registry = registry

    def build(self, stream_callback: Optional[StreamCallback] = stdout_callback) -> Image:
        """Builds and pushes a Docker image to Docker registry."""

    def image_exists(self, tag: str) -> bool:
        """Checks if the image exists in the registry."""
        image = infractl.docker.Image.from_full_name(full_name=tag)
        pd_registry = python_docker.registry.Registry(hostname=self.registry_endpoint)
        try:
            pd_registry.get_manifest(image=image.name, tag=image.tag)
        except requests.exceptions.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                return False
            raise error
        return True

    @property
    def registry_endpoint(self):
        """Registry endpoint."""
        if self.registry:
            if re.search(r'^https?://', self.registry):
                return self.registry
            # Assume that user-specified registry is HTTPS
            return f'https://{self.registry}'
        # Try to detect if running in Kubernetes
        if 'KUBERNETES_SERVICE_HOST' in os.environ:
            return self.registry_internal_endpoint
        else:
            return self.registry_external_endpoint

    @property
    def registry_internal_endpoint(self):
        """Registry internal endpoint."""
        return self.settings(
            'registry_internal_endpoint',
            'http://docker-registry.docker-registry.svc.cluster.local:5000',
        )

    @property
    def registry_external_endpoint(self):
        """Registry internal endpoint."""
        return self.settings(
            'registry_external_endpoint',
            f'http://registry.{self.infrastructure.address}',
        )

    def settings(self, name: str, default_value: Any = None) -> Any:
        """Return a setting value for this infrastructure address."""
        # TODO: this needs to be supported by settings (see also HCL configuration)
        return infractl.base.SETTINGS.get(f'{self.infrastructure.address}.{name}', default_value)


def builder(
    infrastructure: Optional[infractl.base.Infrastructure] = None,
    registry: Optional[str] = None,
    kind: Union[str | BuilderKind] = BuilderKind.AUTO,
):
    """Returns a new Docker image builder.

    Args:
        infrastructure: ICL infrastructure, default one is used when not specified.
        registry: Docker registry, default one from infrastructure is used when not specified.
        kind: kind of Docker builder.
    """
    if isinstance(kind, str):
        kinds = BuilderKind.list()
        if kind.upper() not in kinds:
            raise NotImplementedError(
                f'{kind=} is not supported, possible kinds are {", ".join(kinds).lower()}'
            )
        kind = BuilderKind[kind.upper()]

    if kind == BuilderKind.AUTO:
        if shutil.which('docker'):
            kind = BuilderKind.DOCKER
        else:
            kind = BuilderKind.PREFECT

    if kind == BuilderKind.DOCKER:
        # pylint: disable=import-outside-toplevel, unused-import
        from infractl.docker import local

        return local.Builder(infrastructure=infrastructure, registry=registry)

    if kind == BuilderKind.PREFECT:
        # pylint: disable=import-outside-toplevel, unused-import
        from infractl.docker import remote

        return remote.Builder(infrastructure=infrastructure, registry=registry)

    raise NotImplementedError(f'{kind=} is not supported')
