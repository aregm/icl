"""Prefect flows for testing purpose."""

import time

from prefect import flow, get_run_logger


@flow(persist_result=True)
def flow3(first: str = 'Default Value', second: int = 0):
    logger = get_run_logger()
    logger.info(f'Parameters: {first=}, {second=}')
    # test timeout
    time.sleep(3)
    return first, second


@flow(persist_result=True)
def flow3_with_underscore_in_name():
    # see #28 for details
    return "Some computed value"


@flow(persist_result=True)
def flow3_with_default_storage(first: str = 'Default Value', second: int = 0):
    logger = get_run_logger()
    logger.info(f'Parameters: {first=}, {second=}')
    return first, second
