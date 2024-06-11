import base64
import re
import time

import pytest
import pytest_asyncio
import urllib3
from kubernetes import client, config
from minio import Minio
from minio.error import InvalidResponseError
from prefect.filesystems import RemoteFileSystem
from prefect.infrastructure.kubernetes import KubernetesJob

MINIO_WAIT_TIMEOUT_S = 180


def pytest_addoption(parser):
    parser.addoption(
        "--ray-endpoint",
        action="store",
        default=None,
        type=str,
        help="Name of ray address to use, e.g. ray.jumphost.example.com:443.",
    )

    parser.addoption(
        "--s3-endpoint",
        action="store",
        default=None,
        type=str,
        help="Name of s3 endpoint to use, e.g. s3.jumphost.example.com.",
    )


@pytest.fixture(scope="session")
def ray_endpoint(pytestconfig):
    yield pytestconfig.getoption("--ray-endpoint")


@pytest.fixture(scope="session")
def s3_endpoint(pytestconfig):
    yield pytestconfig.getoption("--s3-endpoint")


@pytest.fixture(scope="session")
def k8s_config():
    """Read kubernetes configuration from ~/.kube"""
    configuration = client.Configuration()
    config.load_kube_config(client_configuration=configuration)
    yield configuration


@pytest.fixture(scope="session")
def minio_credentials(k8s_config):
    """Parse Minio secret to retrieve username and password"""
    api_client = client.api_client.ApiClient(configuration=k8s_config)
    core_v1 = client.CoreV1Api(api_client)
    secret_response = core_v1.read_namespaced_secret(
        name="minio-env-configuration",
        namespace="minio",
    )
    secret_data = base64.b64decode(secret_response.data["config.env"]).splitlines()
    user_regexp = '^export MINIO_ROOT_USER="(.*)"$'
    password_regexp = '^export MINIO_ROOT_PASSWORD="(.*)"$'

    def search_regexp(secret_data, regexp):
        for secret in secret_data:
            m = re.match(regexp, secret.decode("utf-8"))
            if m is not None:
                return m.group(1)
        raise Exception("No secret found that matches regexp " + regexp)

    user = search_regexp(secret_data, user_regexp)
    password = search_regexp(secret_data, password_regexp)
    yield user, password


def remove_s3_bucket(minio_client, bucket_name):
    """Delete test bucket"""

    def remove_directory(name):
        objects = minio_client.list_objects(bucket_name, prefix=name)
        for obj in objects:
            if obj.is_dir:
                remove_directory(obj.object_name)
            else:
                minio_client.remove_object(bucket_name, obj.object_name)

    if minio_client.bucket_exists(bucket_name):
        remove_directory("")
        minio_client.remove_bucket(bucket_name)


@pytest.fixture(scope="session")
def minio_client(s3_endpoint, minio_credentials):
    """Create Minio client object"""
    user, password = minio_credentials
    hc = urllib3.PoolManager(cert_reqs="CERT_NONE")

    if s3_endpoint.find(":") > 0:
        address = s3_endpoint
    else:
        address = f"{s3_endpoint}:80"

    minio_client = Minio(
        address,
        access_key=user,
        secret_key=password,
        secure=False,
        http_client=hc,
    )

    start = time.time()
    success = False
    while time.time() - start < MINIO_WAIT_TIMEOUT_S:
        try:
            minio_client.bucket_exists("random-name")
        except InvalidResponseError:
            time.sleep(1)
        else:
            success = True
            break

    if not success:
        raise Exception("Timed out waiting for minio service to respond")

    yield minio_client


@pytest.fixture(scope="session")
def s3_bucket(minio_client):
    bucket_name = "test-bucket"
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    yield bucket_name
    remove_s3_bucket(minio_client, bucket_name)


@pytest_asyncio.fixture
async def prefect_configure(s3_endpoint, minio_credentials, s3_bucket):
    """Create Prefect configuration documents"""
    user, password = minio_credentials
    fs = RemoteFileSystem(
        # Note the trailing slash, https://github.com/PrefectHQ/prefect/issues/8710
        basepath=f"s3://{s3_bucket}/prefect/test-flow/",
        settings={
            "key": user,
            "secret": password,
            "use_ssl": False,
            "client_kwargs": {"endpoint_url": f"http://{s3_endpoint}"},
        },
    )
    storage_name = "test-flow-storage"
    await fs.save(storage_name, overwrite=True)

    infra = KubernetesJob(
        # By default, Prefect sets pod_watch_timeout_seconds to 60, which is not enough for the case
        # when a custom image is set, and it is not present on the node. Giving more time for Prefect
        # to wait for the pod should help with some test flakiness that we observed in some cases.
        pod_watch_timeout_seconds=240,
        # s3fs is required for Prefect RemoteFileSystem
        env={'EXTRA_PIP_PACKAGES': 's3fs'},
    )
    infra_name = "smoke-check"
    await infra.save(infra_name, overwrite=True)
    yield storage_name, infra_name
