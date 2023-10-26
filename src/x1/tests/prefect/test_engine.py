import os
import pathlib
import uuid

import pytest
from prefect.filesystems import LocalFileSystem

from x1.prefect import engine

SPEC_FILE = """
#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "PWD: $PWD"
echo "TMP: $SCRIPT_DIR"

echo "This is file1" > file1
cp "$SCRIPT_DIR/file2" .
"""


@pytest.mark.asyncio
async def test_run_script(tmp_path: pathlib.Path, set_cwd):
    src = tmp_path / 'src'
    dst = tmp_path / 'dst'

    src.mkdir(parents=True, exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)

    script_path = src / 'entrypoint.sh'
    script_path.write_text(SPEC_FILE)

    file_path = src / 'file2'
    file_path.write_text('This is file2')

    block_name = str(uuid.uuid4())
    block = LocalFileSystem(basepath=src.absolute())
    await block.save(block_name)

    with set_cwd(dst):
        await engine.run_script(f'local-file-system/{block_name}', 'entrypoint.sh')

    file1_path = dst / 'file1'
    file2_path = dst / 'file2'

    assert file1_path.exists()
    assert file2_path.exists()
    assert file1_path.read_text().strip() == 'This is file1'
    assert file2_path.read_text().strip() == 'This is file2'
