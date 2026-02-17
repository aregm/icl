"""Executes a Python program in a container.

Support calling a custom entrypoint (function) in the program. Also handles serialization and
deserialization of program or function parameters and the result.
"""

import argparse
import importlib
import json
import pathlib
import runpy
import sys
from typing import Any

import pydantic.json


def get_full_name(obj: Any) -> str:
    """Returns full name for a Python object."""
    return f'{obj.__module__}.{obj.__qualname__}'


def from_full_name(name: str) -> Any:
    """Returns a Python object for its full name."""
    try:
        return importlib.import_module(name)
    except ImportError:
        if '.' not in name:
            raise

    module_name, member_name = name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, member_name)


def object_encoder(obj: Any) -> Any:
    """Encodes object to JSON."""
    if isinstance(obj, BaseException):
        return {'__exc_type__': get_full_name(obj.__class__), 'message': str(obj)}
    else:
        return {
            '__class__': get_full_name(obj.__class__),
            'data': pydantic.TypeAdapter(type(obj)).dump_python(obj, mode='json'),
        }


def object_decoder(obj: dict) -> Any:
    """Decodes object from JSON."""
    if '__class__' in obj:
        return pydantic.TypeAdapter(from_full_name(obj['__class__'])).validate_python(obj['data'])
    elif '__exc_type__' in obj:
        return from_full_name(obj['__exc_type__'])(obj['message'])
    else:
        return obj


def dumps(obj: Any) -> bytes:
    """Saves object to JSON."""
    result = json.dumps(obj, default=object_encoder)
    if isinstance(result, str):
        # The standard library returns str but others may return bytes directly
        result = result.encode()
    return result


def loads(blob: bytes) -> Any:
    """Loads object from JSON."""
    return json.loads(blob.decode(), object_hook=object_decoder)


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
        help='Entrypoint for a Python program',
    )
    parser.add_argument(
        '--flow',
        required=False,
        help='Prefect flow to execute',
    )
    return parser


def save_result(result: Any):
    """Saves result as JSON."""
    if result is None:
        return
    result_path = pathlib.Path(__file__).resolve().parent / 'result.json'
    with result_path.open(mode='wb') as result_file:
        result_file.write(dumps(result))


def main():
    """Entry point."""
    args = create_parser().parse_args()
    module_name = pathlib.Path(args.program).stem

    # load parameters if present
    parameters = None
    parent = pathlib.Path(__file__).parent
    parameters_path = parent / 'parameters.json'
    if parameters_path.exists():
        with parameters_path.open(mode='rb') as parameters_file:
            parameters = loads(parameters_file.read())
    print('Parameters: ', parameters)

    if args.entrypoint:
        module = importlib.import_module(module_name)
        target = getattr(module, args.entrypoint)
        kwargs = parameters or {}
        save_result(target(**kwargs))

    if args.flow:
        module = importlib.import_module(module_name)
        target = getattr(module, args.flow)
        kwargs = parameters or {}
        save_result(target(**kwargs))

    sys.argv = [args.program]
    if parameters:
        sys.argv.extend(parameters)
    runpy.run_module(module_name, run_name='__main__')


if __name__ == '__main__':
    main()
