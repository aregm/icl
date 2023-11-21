"""Program for Kubernetes runtime.

Loads the program on client side, handles Prefect flows without import and runtime dependency on
Prefect.
"""

import importlib.util
import pathlib
import sys
import warnings
from typing import Any, Optional

from infractl import base


class Program(base.Program):
    """Program for Kubernetes runtime."""

    flow: Optional[str]

    def __init__(self, path: Any, name: Optional[str] = None, flow: Optional[str] = None):
        super().__init__(path=path, name=name)
        self.flow = flow


def load(program: base.Program) -> Program:
    with warnings.catch_warnings():
        # Ignore UserWarning since Prefect complains about loading the same flow definition more
        # than once.
        warnings.simplefilter('ignore', category=UserWarning)
        return _load(program)


def _load(program: base.Program) -> Program:
    """Loads program."""

    if not isinstance(program.path, str):
        raise NotImplementedError(f'{program.path.__class__.__name__} is not supported')

    if not program.path.endswith('.py'):
        raise NotImplementedError(f'Running {program.path} is not supported')

    parent_path = str(pathlib.Path(program.path).resolve().parent)
    current_path = str(pathlib.Path().resolve())

    spec = importlib.util.spec_from_file_location(
        '__infractl_loader__',
        program.path,
        submodule_search_locations=[parent_path, current_path],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules['__infractl_loader__'] = module
    sys.path.insert(0, current_path)
    sys.path.insert(0, parent_path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop('__infractl_loader__')
        sys.path.remove(parent_path)
        sys.path.remove(current_path)

    names = dir(module)

    if program.name:
        if program.name not in names:
            raise ValueError(f'Name "{program.name}" not found in "{program.path}"')
        if is_flow(getattr(module, program.name)):
            return Program(path=program.path, flow=program.name)
        return Program(path=program.path, name=program.name)

    flows = []
    for name in names:
        if is_flow(getattr(module, name)):
            flows.append(name)

    if flows:
        if len(flows) == 1:
            return Program(path=program.path, flow=flows[0])
        else:
            raise ValueError(
                f'More than one flow in "{program.path}", but flow name is not specified'
            )
    else:
        return Program(path=program.path)


def is_flow(obj: Any) -> bool:
    """Checks if the given object is Prefect flow."""
    cls = getattr(obj, '__class__', None)
    if not cls:
        return False
    return (
        getattr(cls, '__name__', None) == 'Flow'
        and getattr(cls, '__module__', None) == 'prefect.flows'
    )
