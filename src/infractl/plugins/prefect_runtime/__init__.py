"""Prefect specific module."""
import re

from infractl.plugins.prefect_runtime.program import (
    PrefectProgram,
    PrefectProgramRun,
    PythonProgram,
    load_program,
)
from infractl.plugins.prefect_runtime.runtime import PrefectRuntimeImplementation


def sanitize(identity: str) -> str:
    """Sanitizes the value to make it compatible with Prefect names."""
    # replace non-alphanumeric characters with '-'
    identity = re.sub('[^0-9a-zA-Z]+', '-', identity.lower())
    # replace repeating '-' with a single one, strip heading and leading '-'
    return re.sub('--+', '-', identity).strip('-')


__all__ = [
    'PrefectRuntimeImplementation',
    'PrefectProgram',
    'PrefectProgramRun',
    'PythonProgram',
    'load_program',
    'sanitize',
]
