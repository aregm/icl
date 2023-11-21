import pathlib

import pytest

import infractl
from infractl.plugins.kubernetes_runtime.program import load

PROGRAM_NO_FLOWS = """
def foo():
    pass
"""

PROGRAM_ONE_FLOW = """
import prefect

@prefect.flow
def my_flow_1():
    pass
"""

PROGRAM_TWO_FLOWS = """
import prefect

@prefect.flow
def my_flow_1():
    pass

@prefect.flow
def my_flow_2():
    pass

if __name__ == '__main__':
    raise Exception('__main__ must not run')
"""


def test_load_valid_name(tmp_path: pathlib.Path):
    program_path = tmp_path / 'program.py'
    program_path.write_text(PROGRAM_NO_FLOWS)
    program = load(infractl.program(program_path, name='foo'))
    assert program.name == 'foo'
    assert program.flow is None


def test_load_invalid_name(tmp_path: pathlib.Path):
    program_path = tmp_path / 'program.py'
    program_path.write_text(PROGRAM_NO_FLOWS)
    with pytest.raises(ValueError):
        load(infractl.program(program_path, name='no_such_name'))


def test_load_one_flow(tmp_path: pathlib.Path):
    program_path = tmp_path / 'program.py'
    program_path.write_text(PROGRAM_ONE_FLOW)
    program = load(infractl.program(program_path))
    assert program.name is None
    assert program.flow == 'my_flow_1'

    program = load(infractl.program(program_path, name='my_flow_1'))
    assert program.name is None
    assert program.flow == 'my_flow_1'


def test_load_two_flows(tmp_path: pathlib.Path):
    program_path = tmp_path / 'program.py'
    program_path.write_text(PROGRAM_TWO_FLOWS)
    with pytest.raises(ValueError):
        load(infractl.program(program_path))

    program = load(infractl.program(program_path, name='my_flow_1'))
    assert program.name is None
    assert program.flow == 'my_flow_1'

    program = load(infractl.program(program_path, name='my_flow_2'))
    assert program.name is None
    assert program.flow == 'my_flow_2'
