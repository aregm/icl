"""ICL infrastructure."""

from __future__ import annotations

from typing import Optional, Tuple, Union

import pydantic

from infractl.base import registry


class Infrastructure(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """Infrastructure specification (for users)."""

    kind: str = pydantic.Field(
        title='Infrastructure kind.',
    )

    address: str = pydantic.Field(
        title='Address of cluster, empty string for the current one',
        default='',
    )

    gpus: Optional[Union[int, Tuple[str, int]]] = pydantic.Field(
        title='Request a number of any GPUs or a specific GPUs.',
        default=None,
    )

    @pydantic.validator('gpus')
    @classmethod
    def _check_gpus_tuple(cls, gpus):
        if isinstance(gpus, int):
            gpus = ('gpu', gpus)
        return gpus


class InfrastructureImplementation(metaclass=registry.RegisteredClass):
    """Infrastructure implementation (for internal usage)."""

    def __init__(
        self,
        infrastructure: Infrastructure,
    ):
        self.infrastructure = infrastructure

    @property
    def address(self) -> str:
        return self.infrastructure.address


def get_infrastructure_implementation(
    infrastructure: Infrastructure,
) -> InfrastructureImplementation:
    infrastructure_implementation_class = registry.RegisteredClass.get(
        InfrastructureImplementation, infrastructure.kind
    )
    return infrastructure_implementation_class(infrastructure)
