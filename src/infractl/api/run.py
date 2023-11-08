"""ICL run (shortcut)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import infractl.base
from infractl.api.deploy import deploy


async def run(
    program: infractl.base.Program,
    runtime: Optional[infractl.base.Runtime] = None,
    infrastructure: Optional[infractl.base.Infrastructure] = None,
    parameters: Union[Dict[str, Any], List[str], None] = None,
    timeout: Optional[float] = None,
    detach: bool = False,
    **kwargs,
) -> infractl.base.ProgramRun:
    """Deploys and runs a program.

    Args:
        program: a program to deploy, can be a file name, ICL program or Prefect Flow instance.
        runtime: an optional program runtime to use for deployment.
        infrastructure: an optional infrastructure to use for deployment.
        parameters: a dictionary of named arguments if a program's entry point is a function,
            a list of arguments otherwise.
        timeout: an optional timeout to use for deployment. This value is the same
            for deploy and run functions.
        detach: `False` (default) to wait for a program completion, `True` to start the program
            and detach from it.
        kwargs: other parameters for deployment.
    """
    deployed_program = await deploy(
        program=program,
        runtime=runtime,
        infrastructure=infrastructure,
        timeout=timeout,
        **kwargs,
    )

    # Run the deployed program
    return await deployed_program.run(parameters=parameters, timeout=timeout, detach=detach)
