"""Prefect flows for testing purpose."""

import os

from prefect import flow, get_run_logger


@flow
def flow4():
    logger = get_run_logger()

    # Check that a Python package is installed
    # pylint: disable=import-outside-toplevel, unused-import
    from prefect_vault import VaultSecret, VaultToken

    # Check that a custom environment variable is set
    env_var = os.environ.get('foo')
    logger.info(f'foo={env_var}')
