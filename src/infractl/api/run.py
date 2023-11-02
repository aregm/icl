"""ICL run (shortcut)"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import infractl.api.infrastructure
import infractl.api.runtime
import infractl.base
from infractl.api.deploy import deploy


async def run(
    program: infractl.base.Program,
    runtime: Optional[infractl.base.Runtime] = None,
    infrastructure: Optional[infractl.base.Infrastructure] = None,
    parameters: Union[Dict[str, Any], List[str], None] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> infractl.base.ProgramRun:
    """Deploys and runs a program by accepting a union of parameters
        from infractl.api.deploy() and infractl.base.program.run()

    Args:
        program: a program to deploy, can be a file name, ICL program or Prefect Flow instance.
        runtime: an optional program runtime to use for deployment.
        infrastructure: an optional infrastructure to use for deployment.
        timeout: an optional timeout to use for deployment. This value is the same
                 for deploy and run functions.
        kwargs: other parameters for deployment.
    """
    deployed_program = await deploy(program, runtime, infrastructure, timeout, **kwargs)

    # Run the deployed program
    return await deployed_program.run(parameters, timeout)
