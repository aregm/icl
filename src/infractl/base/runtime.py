"""ICL runtime."""

from __future__ import annotations

import abc
import os
from typing import Dict, List, Optional

import pydantic

import infractl.base.infrastructure
from infractl.base import registry


class RuntimeDependencies(pydantic.BaseModel):
    """Runtime dependencies.

    Allows declaratively define Python dependencies for different targets,
    such as Prefect, Dask, Ray.
    """

    pip: List[str] = pydantic.Field(
        default_factory=list,
        title='List of pip requirements specifiers',
        description='https://pip.pypa.io/en/stable/reference/requirement-specifiers/',
    )


class RuntimeFile(pydantic.BaseModel):
    """Runtime files.

    Additional files that must exist in the runtime.
    """

    # TODO: support for different schemas, such as 'zip', 's3', and so on
    src: Optional[str] = pydantic.Field(
        default=None,
        title='File source',
        description=(
            'Can be one of: '
            '1. absolute path '
            '2. relative path to the current working directory '
        ),
    )

    dst: Optional[str] = pydantic.Field(
        default=None,
        title='Runtime destination',
        description='Default destination is the runtime current directory',
    )


def parse_dependencies(dependencies: Optional[RuntimeDependencies | Dict]) -> RuntimeDependencies:
    """Parses runtime dependencies."""
    if dependencies is None:
        return RuntimeDependencies()
    if isinstance(dependencies, RuntimeDependencies):
        return dependencies
    if isinstance(dependencies, dict):
        return RuntimeDependencies.parse_obj(dependencies)
    raise NotImplementedError(
        f'{dependencies.__class__.__name__} is not supported as dependency specification'
    )


def parse_files(files: Optional[List[RuntimeFile | Dict | str | os.PathLike]]) -> List[RuntimeFile]:
    """Parses runtime working directory."""
    if files is None:
        return []
    result = []
    for file in files:
        if isinstance(file, str):
            result.append(RuntimeFile(src=file))
        elif isinstance(file, RuntimeFile):
            result.append(file)
        elif isinstance(file, dict):
            # convert os.PathLike to str
            clone = file.copy()
            for key in ('src', 'dst'):
                value = clone.get(key)
                if isinstance(value, os.PathLike):
                    clone[key] = str(value)
            result.append(RuntimeFile.parse_obj(clone))
        elif isinstance(file, os.PathLike):
            result.append(RuntimeFile(src=str(file)))
        else:
            raise NotImplementedError(f'{file.__class__.__name__} is not supported as file item')
    return result


class Runtime:
    """Program runtime specification (for users).

    Allows executing a program in a specific infrastructure.
    """

    def __init__(
        self,
        environment: Optional[Dict[str, str]] = None,
        dependencies: Optional[RuntimeDependencies | Dict] = None,
        files: Optional[List[RuntimeFile | Dict | str]] = None,
        kind: Optional[str] = None,
    ):
        """Creates a new runtime for any compatible infrastructure.

        Args:
            environment: optional dictionary of environment variables
            dependencies: optional runtime dependencies
            files: optional list of runtime files
        """
        self.environment = environment or {}
        self.dependencies = parse_dependencies(dependencies)
        self.files = parse_files(files)
        self.kind = kind


class RuntimeImplementation(metaclass=registry.RegisteredClass):
    """Runtime implementation (for internal usage)."""

    def __init__(
        self,
        runtime: Optional[infractl.base.runtime.Runtime] = None,
        infrastructure_implementation: Optional[
            infractl.base.infrastructure.InfrastructureImplementation
        ] = None,
    ):
        self.runtime = runtime
        self.infrastructure_implementation = infrastructure_implementation

    @abc.abstractmethod
    async def deploy(
        self, program: infractl.base.program.Program, **kwargs
    ) -> infractl.base.DeployedProgram:
        """Deploys a program."""


def get_runtime_implementation(
    runtime: Runtime,
    infrastructure_implementation: infractl.base.infrastructure.InfrastructureImplementation,
) -> RuntimeImplementation:
    runtime_implementation_class = infractl.base.RegisteredClass.get(
        infractl.base.RuntimeImplementation, runtime.kind
    )
    return runtime_implementation_class(runtime, infrastructure_implementation)
