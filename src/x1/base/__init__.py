"""X1 base module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from x1.base.infrastructure import (
    Infrastructure,
    InfrastructureImplementation,
    get_infrastructure_implementation,
)
from x1.base.program import DeployedProgram, Program, ProgramRun, Runnable
from x1.base.registry import RegisteredClass
from x1.base.runtime import (
    Runtime,
    RuntimeDependencies,
    RuntimeFile,
    RuntimeImplementation,
    get_runtime_implementation,
)

if TYPE_CHECKING:
    import dynaconf  # pylint: disable=ungrouped-imports

SETTINGS: dynaconf.Dynaconf


def _settings() -> dynaconf.Dynaconf:
    """Loads settings from the nested package to avoid import-time initialization."""
    # pylint: disable=import-outside-toplevel
    import x1.base.settings as base_settings

    globals()['SETTINGS'] = base_settings.SETTINGS
    return base_settings.SETTINGS


# pylint: disable=invalid-name
def __getattr__(name) -> Any:
    if name == 'SETTINGS':
        return _settings()
    # Implicit else
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = [
    'DeployedProgram',
    'Infrastructure',
    'InfrastructureImplementation',
    'get_infrastructure_implementation',
    'Program',
    'ProgramRun',
    'RegisteredClass',
    'Runnable',
    'Runtime',
    'RuntimeDependencies',
    'RuntimeFile',
    'RuntimeImplementation',
    'get_runtime_implementation',
    'SETTINGS',
]
