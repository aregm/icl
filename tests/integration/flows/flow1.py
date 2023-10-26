"""Prefect flows for testing purpose."""

from prefect import flow, get_run_logger, task


@task
def task_a():
    logger = get_run_logger()
    logger.info('task_a completed')


@task
def task_b():
    logger = get_run_logger()
    logger.info('task_b completed')


@flow
def flow1():
    logger = get_run_logger()
    task_a()
    task_b()
    logger.info('flow completed')
