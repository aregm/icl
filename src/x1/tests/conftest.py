"""Configuration for unit tests."""

import os
import pathlib
from typing import Union

import pytest


class SetCwd:
    """Context manager to temporary change current working directory."""

    cwd: pathlib.Path
    old: pathlib.Path

    def __init__(self, cwd: Union[str, os.PathLike]):
        self.cwd = pathlib.Path(cwd)
        self.old = pathlib.Path().absolute()

    def __enter__(self):
        os.chdir(self.cwd)

    def __exit__(self, *args):
        os.chdir(self.old)


@pytest.fixture
def set_cwd():
    return SetCwd
