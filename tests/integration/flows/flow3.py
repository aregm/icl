"""Prefect flows for testing purpose."""

import time

from prefect import filesystems, flow, get_run_logger


def define_storage():
    result_storage = filesystems.RemoteFileSystem(
        # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
        basepath='s3://prefect/_persistent_results/flow3/',
        settings={
            'key': 'x1miniouser',
            'secret': 'x1miniopass',
            'use_ssl': False,
            'client_kwargs': {'endpoint_url': 'http://s3.localtest.me'},
        },
    )
    return result_storage


@flow(persist_result=True, result_storage=define_storage())
def flow3(first: str = 'Default Value', second: int = 0):
    logger = get_run_logger()
    logger.info(f'Parameters: {first=}, {second=}')
    # test timeout
    time.sleep(3)
    return first, second
