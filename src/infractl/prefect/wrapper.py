"""Wrapper to execute a Python program as a Prefect flow."""

import importlib
import pathlib
import runpy
import sys
from typing import Any, Dict, List, Optional, Union

import prefect


@prefect.flow(log_prints=True)
def wrap(
    program: str,
    entrypoint: Optional[str] = None,
    parameters: Union[Dict[str, Any], List[str], None] = None,
) -> Any:
    """Executes a Python program."""
    logger = prefect.get_run_logger()
    logger.info(f'Running {program=} {entrypoint=}) {parameters=}')
    if entrypoint:
        module = importlib.import_module(pathlib.Path(program).stem)
        target = getattr(module, entrypoint)
        kwargs = parameters or {}
        return target(**kwargs)
    else:
        if parameters:
            sys.argv = [program]
            sys.argv.extend(parameters)
        runpy.run_path(program, run_name='__main__')
