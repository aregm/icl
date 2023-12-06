"""SSH runtime."""

import os
from typing import Any, Dict, List, Optional, Union

import infractl.base
import infractl.plugins.ssh as ssh_plugin
from infractl.plugins.ssh.program import SshProgramRun
from infractl.plugins.ssh.utils import zyme_run_command


class SshProgramRunner(infractl.base.Runnable):
    """SSH program runner."""

    def __init__(
        self,
        program,
        ssh_client,
    ):
        self.program = program
        self.ssh_client = ssh_client

    async def run(
        self,
        parameters: Union[Dict[str, Any], List[str], None] = None,
        timeout: Optional[float] = None,
        detach: bool = False,
    ) -> SshProgramRun:
        """Runs program synchronously."""
        # TODO: if a username is needed to determine a remote path,
        # then this data should be available in this context
        username = os.environ['ICL_SSH_USERNAME']

        # TODO: copying files should be at the time of deployment,
        # and not at the time of run.
        ret_code = zyme_run_command(
            ['python', self.program.path],
            self.ssh_client,
            remotepath=f'/localdisk/{username}/ssh_icl_test/python_script.py',
            overwrite=True,
            # it's not needed for python scripts
            newline_conversion=False,
        )

        # TODO: add message
        # for failing cases
        return SshProgramRun(ret_code == 0)


class SshRuntimeImplementation(infractl.base.RuntimeImplementation, registration_name='ssh'):
    """SSH runtime implementation."""

    def __init__(
        self,
        runtime: Optional[infractl.base.runtime.Runtime] = None,
        infrastructure_implementation: Optional[infractl.base.InfrastructureImplementation] = None,
    ):
        if not isinstance(
            infrastructure_implementation, ssh_plugin.infrastructure.SshInfrastructureImplementation
        ):
            raise NotImplementedError(
                f'{infrastructure_implementation.__class__.__name__} is not supported'
            )
        super().__init__(
            runtime=runtime, infrastructure_implementation=infrastructure_implementation
        )

    async def deploy(
        self,
        program: infractl.base.Program,
        **kwargs,
    ):
        """Deploys a program."""
        ssh_client = self.infrastructure_implementation.get_client()

        deployed_program = infractl.base.DeployedProgram(
            program=program,
            runner=SshProgramRunner(program, ssh_client),
        )

        return deployed_program
