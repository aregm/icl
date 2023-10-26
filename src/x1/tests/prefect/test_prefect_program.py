import pathlib

import pytest

import x1
from x1.plugins.prefect_runtime.program import FlowError, PythonProgram, load_program

FLOW1 = """
import prefect

@prefect.flow
def my_flow_1():
    pass
"""

FLOW2_1 = """
import prefect

@prefect.flow
def my_flow_2_1_1():
    pass

@prefect.flow
def my_flow_2_1_2():
    pass
"""

FLOW2_2 = """
import prefect

@prefect.flow
def my_flow_2_2_1():
    pass

@prefect.flow
def my_flow_2_2_2():
    pass
"""

FLOW3 = """
import prefect

@prefect.flow
def my_flow_3():
    pass
"""

FLOW4 = """
import prefect

@prefect.flow(name='this-is-flow-4')
def my_flow_4():
    pass
"""

PROGRAM1 = """
print('import')

def foo():
    print('foo')

if __name__ == '__main__':
    print('__main__')
"""


def test_load_one_flow_without_name(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flow.py'
    flow_path.write_text(FLOW1)
    program = load_program(flow_path.as_posix())
    assert program.name == 'my-flow-1'


def test_load_two_flows_without_name(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flow.py'
    flow_path.write_text(FLOW2_1)
    with pytest.raises(FlowError):
        _ = load_program(flow_path.as_posix())


def test_load_two_flows_with_name(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flow.py'
    flow_path.write_text(FLOW2_2)
    program = load_program(flow_path.as_posix(), name='my_flow_2_2_1')
    assert program.name == 'my-flow-2-2-1'


def test_load_python_program(tmp_path: pathlib.Path):
    program_path = tmp_path / 'program.py'
    program_path.write_text(PROGRAM1)

    program = load_program(program_path.as_posix())
    assert isinstance(program, PythonProgram)
    assert program.flow.name == 'program'

    program = load_program(program_path.as_posix(), name='foo')
    assert isinstance(program, PythonProgram)
    assert program.flow.name == 'foo'
