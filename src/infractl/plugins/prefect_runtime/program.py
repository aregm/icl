"""ICL Prefect program management."""

from __future__ import annotations

import importlib
import logging
import pathlib
import sys
import warnings
from typing import Any, Dict, List, Optional, Union

import anyio
import prefect
from prefect.client import orchestration
from prefect.client.schemas.filters import LogFilter
from prefect.utilities import importtools

import infractl.base
import infractl.plugins.prefect_runtime.utils as prefect_utils
from infractl.logging import get_logger
from infractl.plugins import prefect_runtime

logger = get_logger()


class FlowError(Exception):
    """Flow error."""


def load_flows(path: str) -> Dict[str, prefect.Flow]:
    """Returns a dictionary of Prefect Flow objects found in the specified path."""
    module = importtools.load_script_as_module(path)
    flows: Dict[str, Any] = {}
    for name in dir(module):
        value = getattr(module, name)
        if isinstance(value, prefect.Flow):
            flows[name] = value
    return flows


class PrefectProgramRun(infractl.base.ProgramRun):
    """Class for checking status and getting results."""

    _flow_run: prefect.client.schemas.FlowRun = None

    def __init__(
        self, flow_run: prefect.client.schemas.FlowRun, prefect_client: orchestration.PrefectClient
    ):
        self._flow_run = flow_run
        self._prefect_client = prefect_client

    def get_flow_run(self) -> prefect.client.schemas.FlowRun:
        return self._flow_run

    async def update(self) -> None:
        self._flow_run = await self._prefect_client.read_flow_run(self._flow_run.id)

    async def wait(self, poll_interval=5) -> None:
        """Wait until the terminal (COMPLETED, CANCELLED, FAILED, CRASHED) state is reached."""
        while True:
            await self.update()
            flow_run = self.get_flow_run()
            if flow_run.state.is_final():
                return
            await anyio.sleep(poll_interval)

    def is_scheduled(self) -> bool:
        return self.get_flow_run().state.is_scheduled()

    def is_pending(self) -> bool:
        return self.get_flow_run().state.is_pending()

    def is_running(self) -> bool:
        return self.get_flow_run().state.is_running()

    def is_completed(self) -> bool:
        return self.get_flow_run().state.is_completed()

    def is_failed(self) -> bool:
        return self.get_flow_run().state.is_failed()

    def is_crashed(self) -> bool:
        return self.get_flow_run().state.is_crashed()

    def is_cancelling(self) -> bool:
        return self.get_flow_run().state.is_running()

    def is_cancelled(self) -> bool:
        return self.get_flow_run().state.is_cancelled()

    def is_final(self) -> bool:
        return self.get_flow_run().state.is_final()

    def is_paused(self) -> bool:
        return self.get_flow_run().state.is_paused()

    def __repr__(self) -> str:
        """Returns a string representation.

        Note that JupyterLab uses __repr__ instead of __str__.
        """
        flow_run = self.get_flow_run()
        return f'{flow_run.name} ({flow_run.state.name})'

    async def logs(self) -> list[str]:
        """View logs for a flow run by ID."""
        # Copied (with modification) from:
        #  @flow_run_app.command()
        #  async def logs(id: UUID, ...):

        flow_run = self.get_flow_run()
        flow_run_id = flow_run.id
        log_filter = LogFilter(flow_run_id={'any_': [flow_run_id]})
        logger.info('Created log filter: %s', log_filter)

        # Get logs by using filter
        page_logs = await self._prefect_client.read_logs(
            log_filter=log_filter,
        )
        logger.info('Received %s logs entries with filter', len(page_logs))

        logs: list[str] = [None] * len(page_logs)
        for idx, log in enumerate(page_logs):
            logs[idx] = (
                f'{log.timestamp} |'
                f' {logging.getLevelName(log.level):7s} | Flow run'
                f' {flow_run.name!r} - {log.message}'
            )
        return logs

    async def stream_logs(self, poll_interval=5, file=None) -> None:
        """
        Stream logs until the terminal (COMPLETED, CANCELLED, FAILED, CRASHED) state is reached.
        """
        timestamp = None
        flow_run = self.get_flow_run()
        flow_run_id = flow_run.id

        while True:
            await self.update()
            flow_run = self.get_flow_run()

            log_filter = LogFilter(
                flow_run_id={'any_': [flow_run_id]}, timestamp={'after_': timestamp}
            )
            logger.info('Created log filter: %s', log_filter)

            # Get logs by using filter
            page_logs = await self._prefect_client.read_logs(
                log_filter=log_filter,
            )
            logger.info('Received %s logs entries with filter', len(page_logs))

            if timestamp and len(page_logs):
                # since `'after_': timestamp` boundary is inclusive we need to drop
                # first log entry to avoid duplication
                page_logs.pop(0)
            logs: list[str] = [None] * len(page_logs)
            for idx, log in enumerate(page_logs):
                logs[idx] = (
                    f'{log.timestamp} |'
                    f' {logging.getLevelName(log.level):7s} | Flow run'
                    f' {flow_run.name!r} - {log.message}'
                )

            for log in logs:
                print(log, file=sys.stdout if file is None else file)

            if flow_run.state.is_final():
                return

            # update timestamp to not receive logs already shown
            if len(page_logs):
                timestamp = page_logs[-1].timestamp

            await anyio.sleep(poll_interval)

    async def cancel(self):
        """Cancel a flow run by ID."""
        await prefect_utils.cancel(self._prefect_client, self.get_flow_run().id)


class PrefectProgram(infractl.base.Program):
    """Prefect program."""

    flow: prefect.Flow
    deployment_name: str = 'infractl'

    def __init__(
        self,
        path: Union[str, prefect.Flow],
        flow: prefect.Flow,
        name: Optional[str] = None,
    ):
        super().__init__(path=path, name=name)
        self.flow = flow


class PythonProgram(PrefectProgram):
    """Python program wrapped as Prefect flow."""

    program: str = ''
    entrypoint: Optional[str] = None
    files: List[infractl.base.RuntimeFile] = []

    def __init__(self, path: str, name: Optional[str] = None):
        # pylint: disable=import-outside-toplevel, unused-import
        from infractl.prefect import wrapper

        program = load_program(path=wrapper.wrap)
        program.flow.name = prefect_runtime.sanitize(name or pathlib.Path(path).stem)
        super().__init__(path=program.path, flow=program.flow)

        program_path = pathlib.Path(path)
        self.program = program_path.name
        self.entrypoint = name
        self.files = [infractl.base.RuntimeFile(src=str(program_path))]


def load_program(
    path: Union[str, prefect.Flow], name: Optional[str] = None, **kwargs
) -> PrefectProgram:
    """Returns Prefect program."""
    with warnings.catch_warnings():
        # Ignore UserWarning since Prefect complains about loading the same flow definition more
        # than once.
        warnings.simplefilter('ignore', category=UserWarning)
        return _load_program(path, name=name, **kwargs)


def _load_program(
    path: Union[str, prefect.Flow], name: Optional[str] = None, **kwargs
) -> PrefectProgram:
    """Returns Prefect program."""

    flow: Optional[prefect.Flow] = None

    if isinstance(path, str):
        flows = load_flows(path)
        if len(flows) == 0:
            # Use a Prefect flow to wrap a Python program
            return PythonProgram(path=path, name=name)
        elif len(flows) > 1:
            if name is None:
                raise FlowError(f'More than one flow in "{path}", but flow name is not specified')
            flow = flows[name]
        else:
            flow = next(iter(flows.values()))

    if isinstance(path, prefect.Flow):
        flow = path
        # TODO: this does not work with a Prefect flow defined in Jupyter notebook: it does
        # not have __file__ or __module__.
        module_name = getattr(flow, '__module__', None)
        if not module_name:
            raise ValueError('Could not determine flow file location (__module__ not set)')
        module = importlib.import_module(module_name)
        path = getattr(module, '__file__', None)
        if not path:
            raise ValueError('Could not determine flow file location (__file__ not set)')

    return PrefectProgram(path=path, flow=flow, name=flow.name, **kwargs)
