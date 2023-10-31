"""ICL program."""

from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Union


class ProgramRun:
    """Class for representing the results and state of ICL program runs."""

    @abc.abstractmethod
    async def wait(self, poll_interval=5) -> None:
        pass

    @abc.abstractmethod
    def is_scheduled(self) -> bool:
        pass

    @abc.abstractmethod
    def is_pending(self) -> bool:
        pass

    @abc.abstractmethod
    def is_running(self) -> bool:
        pass

    @abc.abstractmethod
    def is_completed(self) -> bool:
        pass

    @abc.abstractmethod
    def is_failed(self) -> bool:
        pass

    @abc.abstractmethod
    def is_crashed(self) -> bool:
        pass

    @abc.abstractmethod
    def is_cancelling(self) -> bool:
        pass

    @abc.abstractmethod
    def is_cancelled(self) -> bool:
        pass

    @abc.abstractmethod
    def is_final(self) -> bool:
        pass

    @abc.abstractmethod
    def is_paused(self) -> bool:
        pass


class Program:
    """Program.

    A Program definition that can be deployed to a specific infrastructure with a specific program
    runtime.
    """

    def __init__(self, path: str, name: Optional[str] = None):
        self.path = path
        self.name = name


class Runnable:
    """Runnable."""

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> ProgramRun:
        """Runs this runnable.

        Args:
            parameters: a dictionary of named arguments if a program's entry point is a function,
                a list of arguments otherwise.
            timeout: timeout in seconds to wait for a program completion, `None` (default) to wait
                forever.
            detach: `False` (default) to wait for a program completion, `True` to start the program
                and detach from it.
        """


class DeployedProgram(Runnable):
    """Deployed program."""

    program: Program
    runner: Runnable

    def __init__(self, program: Program, runner: Runnable):
        self.program = program
        self.runner = runner

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> ProgramRun:
        """Runs Program."""
        return await self.runner.run(parameters=parameters, timeout=timeout, detach=detach)
