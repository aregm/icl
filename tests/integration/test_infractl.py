"""
Tests to verify that infractl Python package and ICL cluster work together.

To run the tests you need a local ICL cluster available at `localtest.me`,
see [docs/kind.md](../../docs/kind.md) for the details.
These tests are intended to be executed outside the cluster.

When using HTTP/HTTPS proxy make sure `localtest.me` is added to "no proxy" lists, such as
`NO_PROXY` and `no_proxy`.
"""

import asyncio
import time
from io import StringIO
from unittest.mock import patch

import pytest
from flows.flow2 import flow2

import infractl


@pytest.mark.asyncio
async def test_flow_with_file_name(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program_run = await infractl.run(
        infractl.program('flows/flow1.py'), runtime=runtime, infrastructure=infrastructure
    )
    assert program_run.is_completed()
    assert 'Completed' in str(program_run), '__str__ for ProgramRun returns state'


@pytest.mark.asyncio
async def test_flow_with_imported_module(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program(flow2),
        runtime=runtime,
        infrastructure=infrastructure,
    )
    program_run = await program.run()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_flow_without___file__(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()

    # assumed prefect logic (if no entrypoint passed)
    # flow_file = getattr(flow, "__globals__", {}).get("__file__")
    # mod_name = getattr(flow, "__module__", None)
    # if not flow_file:
    #    if not mod_name:
    #        raise ValueError
    #    try:
    #        module = importlib.import_module(mod_name)
    #        flow_file = getattr(module, "__file__", None)
    # ------------------------------------------------------
    # To be sure that changing the prefect won't break infractl, we can test if
    # `deploy` works without `__module__` (and therefore without `__file__`).
    # Note: `__globals__` is also not defined by default for `prefect.Flow` object.
    program = infractl.program(flow2)
    with patch.object(program.flow, "__module__", new=None):
        program = await infractl.deploy(program, runtime=runtime, infrastructure=infrastructure)
        program_run = await program.run()
        assert program_run.is_completed()


@pytest.mark.asyncio
@pytest.mark.parametrize('flow_name', ['flow3', 'flow3_with_default_storage'])
async def test_flow_with_parameters(address, flow_name):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow3.py', name=flow_name),
        name=f'{flow_name}-with-parameters',
        infrastructure=infrastructure,
    )
    program_run = await program.run(
        parameters={
            'first': '1',
            'second': 2,
        },
    )
    assert program_run.is_completed()
    assert await program_run.result() == ('1', 2)


@pytest.mark.asyncio
async def test_failing_flow(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow6.py'),
        infrastructure=infrastructure,
    )
    program_run = await program.run()
    assert program_run.is_failed()


@pytest.mark.asyncio
async def test_flow_timeout(address):
    infrastructure = infractl.infrastructure(address=address)
    # Deploy and run a flow in a local infractl cluster
    program = await infractl.deploy(
        infractl.program('flows/flow3.py', name='flow3'),
        name='flow3-with-timeout',
        infrastructure=infrastructure,
    )
    with pytest.raises(asyncio.exceptions.TimeoutError):
        await program.run(timeout=1)


@pytest.mark.asyncio
async def test_flow_with_complex_name(address):
    infrastructure = infractl.infrastructure(address=address)
    # Deploy and run a flow in a local infractl cluster
    program = await infractl.deploy(
        infractl.program('flows/flow3.py', name='flow3_with_underscore_in_name'),
        name='flow3_with_underscore_in_name',
        infrastructure=infrastructure,
    )
    program_run = await program.run()
    assert program_run.is_completed()
    assert await program_run.result() == "Some computed value"


@pytest.mark.asyncio
async def test_flow_async(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow3.py', name='flow3'),
        name='flow3-async',
        infrastructure=infrastructure,
    )
    program_run = await program.run(detach=True)
    assert program_run.is_scheduled()

    for i in range(60):
        if program_run.is_running():
            break
        time.sleep(1)
        await program_run.update()
    else:
        raise RuntimeError("the program has been in the planned state for too long")

    await program_run.cancel()
    print(f"program_run=")
    assert program_run.is_cancelling()

    for i in range(60):
        if program_run.is_cancelled():
            break
        time.sleep(1)
        await program_run.update()
    else:
        raise RuntimeError("the program has been in the planned state for too long")


@pytest.mark.asyncio
async def test_flow_async_and_wait(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow3.py', name='flow3'),
        name='flow3-async-and-wait',
        infrastructure=infrastructure,
    )
    program_run = await program.run(detach=True)
    assert program_run.is_scheduled()
    await program_run.wait()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_flow_with_tags(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow1.py'),
        name='flow1-with-tags',
        infrastructure=infrastructure,
        tags=['tag1'],
    )


@pytest.mark.asyncio
async def test_flow_with_schedule(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow1.py'),
        name='flow1-with-cron',
        infrastructure=infrastructure,
        schedule={'cron': '0 0 * * *'},
    )


@pytest.mark.asyncio
async def test_get_logs_from_program_run(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow1.py'),
        name='flow1-test-get-logs',
        infrastructure=infrastructure,
    )
    program_run = await program.run()
    assert program_run.is_completed()
    actual_logs = await program_run.logs()
    print(actual_logs)
    expected_messages = ['task_a completed', 'task_b completed', 'flow completed']
    for expected_message in expected_messages:
        # look for the expected messages in the form of a substring among all logs
        assert any(expected_message in actual_log for actual_log in actual_logs)


@pytest.mark.asyncio
async def test_stream_logs_from_program_run(address):
    infrastructure = infractl.infrastructure(address=address)
    program = await infractl.deploy(
        infractl.program('flows/flow7.py'),
        name='flow7-test-stream-logs',
        infrastructure=infrastructure,
    )
    program_run = await program.run(detach=True)

    # emulate sys.stdout
    file = StringIO()
    await program_run.stream_logs(file=file)

    file.seek(0)
    logs = file.read()
    print(f"{logs=}")

    for idx in range(60):
        substring = f"Iteration: {idx}\n"
        pos = logs.find(substring)
        # check if the logs contains the log entry
        assert pos != -1
        pos = logs.find(substring, pos + len(substring))
        # should be only once
        assert pos == -1


@pytest.mark.asyncio
async def test_flow_with_dependencies(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime(
        environment={'foo': 'bar'},
        dependencies={'pip': ['prefect-vault']},
    )
    program = await infractl.deploy(
        infractl.program('flows/flow4.py'), runtime=runtime, infrastructure=infrastructure
    )
    program_run = await program.run()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_flow_with_files(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime(
        files=[
            # file from local current directory to runtime working directory
            'data/test_file.txt',
            # file from local current directory to runtime working directory with different name
            {'src': 'data/test_file.txt', 'dst': 'test_file.txt.renamed'},
            # 'data/' from local current directory to 'new_data/' in runtime working directory
            {'src': 'data/', 'dst': 'new_data/'},
        ],
    )
    program = await infractl.deploy(
        infractl.program('flows/flow5.py'), runtime=runtime, infrastructure=infrastructure
    )
    program_run = await program.run()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_flow_with_customizations(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()

    customizations = [
        {
            'op': 'add',
            'path': '/spec/ttlSecondsAfterFinished',
            'value': 600,
        },
    ]

    program = await infractl.deploy(
        infractl.program('flows/flow2.py'),
        name='flow2-with-customizations',
        runtime=runtime,
        infrastructure=infrastructure,
        customizations=customizations,
    )
    program_run = await program.run()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_python_program(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program_run = await infractl.run(
        infractl.program('flows/program1.py'), runtime=runtime, infrastructure=infrastructure
    )
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_python_program_with_parameters(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program_run = await infractl.run(
        infractl.program('flows/program1.py'),
        runtime=runtime,
        infrastructure=infrastructure,
        name='program-with-parameters',
        parameters=['arg1', 'arg2'],
    )
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_python_function(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program('flows/program1.py', name='foo'),
        runtime=runtime,
        infrastructure=infrastructure,
        name='program-with-entrypoint',
    )
    program_run = await program.run()
    assert program_run.is_completed()


@pytest.mark.asyncio
async def test_python_function_with_parameters(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program('flows/program1.py', name='foo'),
        runtime=runtime,
        infrastructure=infrastructure,
        name='function-with-parameters',
    )
    program_run = await program.run(parameters={'arg1': 'val1'})
    assert program_run.is_completed()
