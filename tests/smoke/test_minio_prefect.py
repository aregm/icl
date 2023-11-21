import io
import time

import pytest
from prefect.client import get_client
from prefect.deployments import Deployment
from prefect.filesystems import RemoteFileSystem
from prefect.infrastructure.kubernetes import KubernetesJob
from utils import prefect_test_flow

FLOW_RUN_TIMEOUT_S = 480


class PrefectError(Exception):
    """Prefect error."""


def test_minio(minio_client, s3_bucket):
    test_object_name = "test-object.txt"
    if test_object_name in [x.object_name for x in minio_client.list_objects(s3_bucket)]:
        minio_client.remove_object(s3_bucket, test_object_name)

    test_object_contents = "some data111"
    minio_client.put_object(
        s3_bucket,
        test_object_name,
        io.BytesIO(test_object_contents.encode("utf-8")),
        len(test_object_contents),
        "text/plain",
    )

    try:
        response = minio_client.get_object(s3_bucket, test_object_name)
        contents = response.data.decode()
        assert (
            contents == test_object_contents
        ), f'Downloaded data is wrong: "{contents}", should be "{test_object_contents}"'
    finally:
        response.close()
        response.release_conn()


@pytest.mark.asyncio
async def test_prefect(prefect_configure):
    """Run Prefect test"""
    storage_name, infra_name = prefect_configure
    storage = await RemoteFileSystem.load(storage_name)
    infra = await KubernetesJob.load(infra_name)
    deployment = await Deployment.build_from_flow(
        flow=prefect_test_flow,
        name="test-flow111",
        storage=storage,
        infrastructure=infra,
        work_queue_name="prod",
    )
    await deployment.update(entrypoint="utils.py:prefect_test_flow")
    await deployment.upload_to_storage(f"remote-file-system/{storage_name}")
    deployment_id = await deployment.apply()

    client = get_client()
    flow_run = await client.create_flow_run_from_deployment(deployment_id)
    flow_run_id = flow_run.id
    for t in range(0, FLOW_RUN_TIMEOUT_S):
        time.sleep(1)
        flow_run = await client.read_flow_run(flow_run_id)
        if flow_run.end_time is not None:
            state = flow_run.state
            if state.is_completed():
                return
            else:
                raise PrefectError(f"Bad flow state: {state}")
    raise PrefectError("Flow timed out")
