"""ICL program."""

import os
from typing import Optional

import infractl.base


def program(path, name: Optional[str] = None) -> infractl.base.Program:
    """Create a program.

    Args:
        path: program to deploy, location or function.
        name: optional entrypoint in the program.

    Examples:
        1. Python file with Prefect flow:

            program('my_flow.py')

        2. Imported Prefect flow:

            from my_flow import flow1
            program(flow1)
    """
    if isinstance(path, os.PathLike):
        path = str(path)
    return infractl.base.Program(path=path, name=name)
