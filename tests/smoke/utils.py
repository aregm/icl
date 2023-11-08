from prefect import flow, get_run_logger

MINIO_API_PORT = 80
MINIO_WAIT_TIMEOUT_S = 180

PREFECT_IMAGE_NAME = "pbchekin/icl-prefect:2.13.6-py3.9-icl0.0.3"
FLOW_RUN_TIMEOUT_S = 480


@flow
def prefect_test_flow():
    """Test flow"""
    logger = get_run_logger()
    logger.info("This is a test flow")
    flow_result = "flow successfull"
    return flow_result
