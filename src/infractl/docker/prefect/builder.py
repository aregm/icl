"""Prefect flow to build and push Docker image."""

import io
import os
import re
import signal
import subprocess
import time
from typing import Any, Dict

import prefect


class BuildError(Exception):
    """Build error."""


def wait_docker(timeout=600):
    """Waits for Docker daemon.

    Since we run dind in a separate container it takes some time for dind to start and generate
    client certificates, so there is a retry loop.
    """
    # import locally to avoid dependency on psutil when deploying this flow.
    # pylint: disable=import-outside-toplevel
    import psutil

    logger = prefect.get_run_logger()
    logger.info('Waiting for dockerd')
    for retry in range(timeout):
        dockerd_pid = [
            process.pid for process in psutil.process_iter() if process.name() == 'dockerd'
        ]
        if dockerd_pid:
            logger.info('dockerd is running')
            break
        time.sleep(1)
    else:
        raise BuildError(f'dockerd is not running after {timeout} seconds, giving up')

    for _ in range(max(timeout - retry, 1)):
        # pylint: disable=subprocess-run-check
        process = subprocess.run(['docker', 'info'], capture_output=True)
        if process.returncode == 0:
            logger.info('dockerd is responding')
            return
        time.sleep(1)

    raise BuildError(f'dockerd is not responding after {timeout} seconds, giving up')


def kill_docker(timeout=30):
    """Kills Docker daemon.

    Docker daemon is running in a separate container, but in the same pod. This pod has
    `shareProcessNamespace` set to true, so we can see the processes from other container and send
    a signal to terminate.

    Args:
        timeout: timeout in seconds to wait for docker termination.
    """
    # import locally to avoid dependency on psutil when deploying this flow.
    # pylint: disable=import-outside-toplevel
    import psutil

    logger = prefect.get_run_logger()
    docker_init_pid = [
        process.pid for process in psutil.process_iter() if process.name() == 'docker-init'
    ]
    if not docker_init_pid:
        logger.info('docker-init not found, nothing to do')
        return

    logger.info('Terminating docker-init and waiting for docker processes to finish')
    os.kill(docker_init_pid[0], signal.SIGTERM)
    docker_processes = []
    for _ in range(timeout):
        docker_processes = [
            process.name()
            for process in psutil.process_iter()
            if process.name() in ('docker-init', 'dockerd', 'containerd')
        ]
        if not docker_processes:
            logger.info('Docker has been terminated, exiting')
            return
        time.sleep(1)
    logger.info(f'Giving up after waiting {timeout}s for docker processes to finish, exiting')
    logger.info(f'Remaining processes: {", ".join(docker_processes)}')


@prefect.flow(log_prints=True)
def build(build_args: Dict[str, Any], registry: str):
    """Builds and pushes Docker image."""
    logger = prefect.get_run_logger()
    logger.info(f'{build_args=}')

    tag = build_args['tag']
    registry = re.sub(r'^https?://', '', registry)
    full_tag = f'{registry}/{tag}'

    try:
        wait_docker()

        with subprocess.Popen(
            ['docker', 'build', '--tag', full_tag, 'context'],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        ) as process:
            for line in io.TextIOWrapper(process.stdout, encoding='utf-8'):
                print(line.rstrip())
            process.wait()
            if process.returncode != 0:
                raise BuildError('Build failed')

        with subprocess.Popen(
            ['docker', 'push', full_tag],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        ) as process:
            for line in io.TextIOWrapper(process.stdout, encoding='utf-8'):
                print(line.rstrip())
            process.wait()
            if process.returncode != 0:
                raise BuildError('Push failed')
    finally:
        kill_docker()
