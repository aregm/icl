import time

import pytest
import requests
from kubernetes import client, config, stream


def pytest_addoption(parser):
    parser.addoption(
        '--address',
        action='store',
        default='localtest.me',
        type=str,
        help='ICL infrastructure address, default: localtest.me',
    )
    parser.addoption(
        '--jupyterhub-namespace',
        action='store',
        default='jupyterhub',
        type=str,
        help='ICL infrastructure address, default: jupyterhub',
    )


@pytest.fixture(scope='session')
def address(pytestconfig):
    yield pytestconfig.getoption('--address')


@pytest.fixture(scope='session')
def jupyterhub_namespace(pytestconfig):
    yield pytestconfig.getoption('--jupyterhub-namespace')


@pytest.fixture(scope="session")
def jupyterhub_session_pod_name(jupyterhub_namespace, address):
    """Creates a new JupyterHub session and returns a pod name for this session."""
    username = 'test'
    jupyterhub_address = f"jupyter.{address}"
    jupyterhub_url = f"http://{jupyterhub_address}/hub"
    jupyterhub_login_page = f"{jupyterhub_url}/login"
    jupyterhub_api_url = f"{jupyterhub_url}/api"

    http_session = requests.session()
    r = http_session.get(jupyterhub_login_page)
    assert r.status_code == 200
    xsrf_token = http_session.cookies['_xsrf']

    payload = {'_xsrf': xsrf_token, 'username': username, 'password': ""}
    r = http_session.post(jupyterhub_login_page, data=payload)
    assert r.status_code == 200

    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    hub_all_pods = core_v1.list_namespaced_pod(
        namespace=jupyterhub_namespace, label_selector='component=hub'
    )
    assert len(hub_all_pods.items) == 1

    hub_pod = hub_all_pods.items[0]

    command = ['/bin/sh', '-c', f'jupyterhub token {username}']
    jupyterhub_token = stream.stream(
        core_v1.connect_get_namespaced_pod_exec,
        hub_pod.metadata.name,
        jupyterhub_namespace,
        command=command,
        stderr=False,
        stdin=False,
        stdout=True,
        tty=False,
    ).strip()

    assert len(jupyterhub_token) == 32

    for _ in range(30):
        r = requests.post(
            jupyterhub_api_url + f'/users/{username}/server',
            headers={'Authorization': f'token {jupyterhub_token}'},
            json={'name': username},
        )
        try:
            response_json = r.json()
            # Wait for "session is already started" code
            if response_json['status'] == 400:
                break
        except requests.exceptions.JSONDecodeError:
            pass
        time.sleep(5)

    assert (
        r.status_code == 400
    ), f'Request to {r.url}: got {r.status_code}, expected: 400. Response: {r.text}'

    jupyter_all_test_user_pods = core_v1.list_namespaced_pod(
        namespace=jupyterhub_namespace, label_selector=f'hub.jupyter.org/username={username}'
    ).items
    assert len(jupyter_all_test_user_pods) == 1

    return jupyter_all_test_user_pods[0].metadata.name
