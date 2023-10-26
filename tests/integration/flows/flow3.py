"""Prefect flows for testing purpose."""

import time

from prefect import flow, get_run_logger


@flow
def flow3(first: str = 'Default Value', second: int = 0):
    logger = get_run_logger()
    logger.info(f'Parameters: {first=}, {second=}')
    # test timeout
    time.sleep(3)
