"""SSH program management."""

from typing import Any, Optional

import infractl
from infractl import base


class SshProgramRun(infractl.base.ProgramRun):
    """Class for checking status and getting results."""

    # entity to access program run

    completed: bool
    message: Optional[str]

    def __init__(self, completed: bool = True, message: Optional[str] = None):
        self.completed = completed
        self.message = message

    def is_scheduled(self) -> bool:
        return True

    def is_pending(self) -> bool:
        return False

    def is_running(self) -> bool:
        return False

    def is_completed(self) -> bool:
        return self.completed

    def is_failed(self) -> bool:
        return not self.completed

    def is_crashed(self) -> bool:
        return False

    def is_cancelling(self) -> bool:
        return False

    def is_cancelled(self) -> bool:
        return False

    def is_final(self) -> bool:
        return True

    def is_paused(self) -> bool:
        return False

    async def wait(self, poll_interval=5) -> None:
        raise NotImplementedError()


class Program(base.Program):
    """Program for Kubernetes runtime."""

    flow: Optional[str]

    def __init__(self, path: Any, name: Optional[str] = None, flow: Optional[str] = None):
        super().__init__(path=path, name=name)
        self.flow = flow
