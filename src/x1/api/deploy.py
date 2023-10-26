"""X1 deploy functionality."""


from __future__ import annotations

import asyncio
from typing import Optional

import x1.api.infrastructure
import x1.api.runtime
import x1.base


async def deploy(
    program: x1.base.Program,
    runtime: Optional[x1.base.Runtime] = None,
    infrastructure: Optional[x1.base.Infrastructure] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> x1.base.DeployedProgram:
    """Deploys a program.

    Args:
        program: a program to deploy, can be a file name, X1 program or Prefect Flow instance.
        runtime: an optional program runtime to use for deployment.
        infrastructure: an optional infrastructure to use for deployment.
        timeout: an optional timeout to use for deployment.
        kwargs: other parameters for deployment.
    """
    if not isinstance(program, x1.base.Program):
        raise NotImplementedError(f"{program=} don't supported")

    if infrastructure is None:
        infrastructure = x1.api.infrastructure.default_infrastructure()

    if runtime is None:
        runtime = x1.api.runtime.default_runtime()

    infrastructure_implementation = x1.base.get_infrastructure_implementation(infrastructure)
    runtime_implementation = x1.base.get_runtime_implementation(
        runtime, infrastructure_implementation
    )

    return await asyncio.wait_for(runtime_implementation.deploy(program, **kwargs), timeout=timeout)
