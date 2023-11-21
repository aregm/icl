from prefect import flow, get_run_logger


@flow
def prefect_test_flow():
    """Test flow"""
    logger = get_run_logger()
    logger.info("This is a test flow")
    flow_result = "flow successfull"
    return flow_result
