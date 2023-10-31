"""Utils for Prefect runtime."""

from prefect.client.schemas.objects import StateType
from prefect.client.schemas.responses import SetStateStatus
from prefect.exceptions import ObjectNotFound
from prefect.states import State

from infractl.logging import get_logger

logger = get_logger()


async def cancel(prefect_client, flow_id):
    """Cancel a flow run by ID."""
    # Copied (with modification) from:
    #  @flow_run_app.command()
    #  async def cancel(id: UUID):
    cancelling_state = State(type=StateType.CANCELLING)
    try:
        result = await prefect_client.set_flow_run_state(
            flow_run_id=flow_id, state=cancelling_state
        )
    except ObjectNotFound as exc:
        raise RuntimeError(f"Flow run '{flow_id}' not found!") from exc

    if result.status == SetStateStatus.ABORT:
        raise RuntimeError(
            f"Flow run '{flow_id}' was unable to be cancelled. "
            + f"Reason: '{result.details.reason}'"
        )

    logger.info("Flow run with id: '%s' was successfully scheduled for cancellation.", flow_id)
