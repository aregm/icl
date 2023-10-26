import os
import pathlib
import shutil
import time
import uuid

import pytest

import x1
from x1 import docker

DOCKERFILE = """
FROM scratch

COPY test_file .
"""


@pytest.mark.skipif(shutil.which('docker') is None, reason='requires local Docker')
def test_local_builder(tmp_path: pathlib.Path, address):
    # NOTE: this test creates a new Docker image with a unique tag. It is expected that is executed
    # against a short living cluster, otherwise all images 'test_local_builder:*' need to be
    # deleted manually.
    tag = f'test_local_builder:{uuid.uuid4()}'
    (tmp_path / 'Dockerfile').write_text(DOCKERFILE)
    (tmp_path / 'test_file').write_text('test file')

    builder = docker.builder(
        infrastructure=x1.infrastructure(address=address),
        kind='docker',
    )

    assert not builder.image_exists(tag), 'image does not exist before build'

    image = builder.build(
        path=str(tmp_path),
        tag=tag,
    )

    assert image.full_name == tag


def test_remote_builder(tmp_path: pathlib.Path, address):
    # NOTE: this test creates a new Docker image with a unique tag. It is expected that is executed
    # against a short living cluster, otherwise all images 'test_remote_builder:*' need to be
    # deleted manually.
    tag = f'test_remote_builder:{uuid.uuid4()}'
    (tmp_path / 'Dockerfile').write_text(DOCKERFILE)
    (tmp_path / 'test_file').write_text('test file')

    builder = docker.builder(
        infrastructure=x1.infrastructure(address=address),
        kind='prefect',
    )

    assert not builder.image_exists(tag), 'image does not exist before build'

    image = builder.build(
        path=str(tmp_path),
        tag=tag,
    )

    assert image.full_name == tag


def wait_for_image(builder, tag: str, retries: int = 10):
    for i in range(retries):
        if builder.image_exists(tag):
            return
        time.sleep(1)
    raise AssertionError(f'image {tag} does not exists after build after {retries} retries')
