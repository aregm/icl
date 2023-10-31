"""Wrapper for Prefect engine."""

import argparse
import asyncio
import pathlib
import runpy
import subprocess
import sys
import tempfile


async def run_script(block: str, script: str):
    """Downloads a directory from Prefect storage block and executes a shell script.

    Downloads a directory from the specified Prefect storage block and executes a shell script with
    the specified name in directory. The script is executed in the current directory, it can access
    other files in the temporary directory with:

    ```
    # https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    ```
    """
    # pylint: disable=import-outside-toplevel
    import prefect.blocks.core as blocks

    print(f'[infractl.prefect.engine] Loading Prefect storage block {block}')
    storage = await blocks.Block.load(block)
    with tempfile.TemporaryDirectory() as dirname:
        await storage.get_directory(local_path=dirname)
        script_path = pathlib.Path(dirname) / script
        if script_path.exists():
            print(f'[infractl.prefect.engine] Running script {script}')
            subprocess.run(
                ['/bin/bash', '-x', script_path.absolute()],
                stdout=sys.stdout,
                stderr=subprocess.STDOUT,
                check=True,
            )
        else:
            print(f'[infractl.prefect.engine] Script {block} not found')


def create_parser() -> argparse.ArgumentParser:
    """Creates argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--block', help='Download a directory from this storage block and execute a shell script'
    )
    parser.add_argument(
        '--script',
        default='entrypoint.sh',
        help='Script name to execute (default is "entrypoint.sh")',
    )
    return parser


def main():
    """Entry point."""
    args = create_parser().parse_args()
    if args.block:
        asyncio.run(run_script(args.block, args.script))
    # Delete all command line arguments, prefect.engine does not need them
    sys.argv = sys.argv[0:1]
    runpy.run_module('prefect.engine', run_name='__main__')


if __name__ == '__main__':
    main()
