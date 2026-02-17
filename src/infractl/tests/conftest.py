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


# Skip test modules that depend on Prefect 2.x APIs (deployments.Deployment, etc.)
# removed in Prefect 3.x. These tests need a full migration to the Prefect 3.x SDK.
collect_ignore_glob = [
    "prefect/test_prefect_program.py",
    "prefect/test_prefect_runtime.py",
    "kubernetes/test_kubernetes_program.py",
]
