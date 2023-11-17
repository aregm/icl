"""Executes a Python program in a container.

Support calling a custom entrypoint (function) in the program. Also handles serialization and
deserialization of program or function parameters and the result.
"""

import argparse
import importlib
import pathlib
import runpy


def create_parser() -> argparse.ArgumentParser:
    """Creates argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'program',
        help='Python program to execute',
    )
    parser.add_argument(
        '--entrypoint',
        required=False,
        help='Download a directory from this storage block and execute a shell script',
    )
    return parser


def main():
    """Entry point."""
    args = create_parser().parse_args()
    module_name = pathlib.Path(args.program).stem
    if args.entrypoint:
        module = importlib.import_module(module_name)
        target = getattr(module, args.entrypoint)
        return target()
    runpy.run_module(module_name, run_name='__main__')


if __name__ == '__main__':
    main()
