"""Prefect flows for testing purpose."""

import time

from prefect import flow, get_run_logger


@flow
def flow7():
    logger = get_run_logger()
    for idx in range(60):
        logger.info(f'Iteration: {idx}')
        time.sleep(1)
