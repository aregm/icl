"""ICL deploy."""


from __future__ import annotations

import asyncio
from typing import Optional

import infractl.api.infrastructure
import infractl.api.runtime
import infractl.base


async def deploy(
    program: infractl.base.Program,
    runtime: Optional[infractl.base.Runtime] = None,
    infrastructure: Optional[infractl.base.Infrastructure] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> infractl.base.DeployedProgram:
    """Deploys a program.

    Args:
        program: a program to deploy, can be a file name, ICL program or Prefect Flow instance.
        runtime: an optional program runtime to use for deployment.
        infrastructure: an optional infrastructure to use for deployment.
        timeout: an optional timeout to use for deployment.
        kwargs: other parameters for deployment.
    """
    if not isinstance(program, infractl.base.Program):
        raise NotImplementedError(f"{program=} don't supported")

    if infrastructure is None:
        infrastructure = infractl.api.infrastructure.default_infrastructure()

    if runtime is None:
        runtime = infractl.api.runtime.default_runtime()

    infrastructure_implementation = infractl.base.get_infrastructure_implementation(infrastructure)
    runtime_implementation = infractl.base.get_runtime_implementation(
        runtime, infrastructure_implementation
    )

    return await asyncio.wait_for(runtime_implementation.deploy(program, **kwargs), timeout=timeout)
