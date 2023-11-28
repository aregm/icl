import datetime
import json
import time

import requests
from kubernetes import client, config
from kubernetes.stream import stream
from pytest import fixture, mark

TEST_USERNAME = "test"
JUPYTERHUB_NAMESPACE = "jupyterhub"
IPYNB_TEST_FILE_PATH = "data/test_notebook.ipynb"


def exec_into_pod(api, pod_name, namespace, command):
    return stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=command,
        stderr=False,
        stdin=False,
        stdout=True,
        tty=False,
    )


# https://github.com/kubernetes-client/python/issues/476#issuecomment-375056804
def copy_file_to_pod(api, pod_name, namespace, source_file, destination_file):
    exec_command = ['/bin/sh']
    resp = stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=exec_command,
        stderr=True,
        stdin=True,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
    buffer = b''
    with open(source_file, "rb") as file:
        buffer += file.read()

    commands = []
    commands.append(bytes("cat <<'EOF' >" + destination_file + "\n", 'utf-8'))
    commands.append(buffer)
    commands.append(bytes("EOF\n", 'utf-8'))

    while resp.is_open():
        resp.update(timeout=1)
        if commands:
            cmd = commands.pop(0)
            resp.write_stdin(cmd)
        else:
            break
    assert len(commands) == 0
    resp.close()

    # TODO: "cat <<EOF" the test notebook file into the container
    # TODO: run the notebook and evaluate results


def test_create_jupyter_session(address):
    jupyterhub_address = f"jupyter.{address}"
    jupyterhub_url = f"http://{jupyterhub_address}/hub"
    jupyterhub_login_page = f"{jupyterhub_url}/login"
    jupyterhub_api_url = f"{jupyterhub_url}/api"

    http_session = requests.session()
    r = http_session.get(jupyterhub_login_page)
    assert r.status_code == 200
    xsrf_token = http_session.cookies['_xsrf']

    payload = {'_xsrf': xsrf_token, 'username': TEST_USERNAME, 'password': ""}
    r = http_session.post(jupyterhub_login_page, data=payload)
    assert r.status_code == 200

    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    hub_all_pods = core_v1.list_namespaced_pod(
        namespace=JUPYTERHUB_NAMESPACE, label_selector='component=hub'
    )
    assert len(hub_all_pods.items) == 1

    hub_pod = hub_all_pods.items[0]

    exec_command = ['/bin/sh', '-c', f'jupyterhub token {TEST_USERNAME}']
    jupyterhub_token = exec_into_pod(
        core_v1, hub_pod.metadata.name, JUPYTERHUB_NAMESPACE, exec_command
    ).strip()
    assert len(jupyterhub_token) == 32

    retries = 12
    i = 0
    data = {'name': TEST_USERNAME}
    response_json = {}
    while i < retries:
        r = requests.post(
            jupyterhub_api_url + f'/users/{TEST_USERNAME}/server',
            headers={'Authorization': f'token {jupyterhub_token}'},
            json=data,
        )
        try:
            response_json = r.json()
            # Wait for "session is already started" code
            if response_json['status'] == 400:
                break
        except requests.exceptions.JSONDecodeError:
            pass
        time.sleep(10)
        i = i + 1
    assert (
        r.status_code == 400
    ), f'Request to {r.url}: status {r.status_code}, should be "400 (session already running)". Response: {r.text}'

    jupyter_all_test_user_pods = core_v1.list_namespaced_pod(
        namespace=JUPYTERHUB_NAMESPACE, label_selector=f'hub.jupyter.org/username={TEST_USERNAME}'
    ).items
    assert len(jupyter_all_test_user_pods) == 1

    jupyter_test_pod = jupyter_all_test_user_pods[0]

    copy_file_to_pod(
        core_v1,
        jupyter_test_pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        IPYNB_TEST_FILE_PATH,  # relative to tests/integration
        "/tmp/test_notebook.ipynb",
    )

    # In order to execute NB inside the python-3.9 conda environment, we install nbconvert to this "user" environment.
    # There is a better way to do this.
    exec_into_pod(
        core_v1,
        jupyter_test_pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        [
            "/bin/bash",
            "-c",
            "{ ~/.conda/bin/conda install -n python-3.9 -y nbconvert && \
         ~/.conda/bin/conda run -n python-3.9 \
            jupyter nbconvert /tmp/test_notebook.ipynb --execute --to notebook; } > /tmp/nbconvert.log 2>&1",
        ],
    )

    output = exec_into_pod(
        core_v1,
        jupyter_test_pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        ["/bin/cat", "/tmp/test_notebook.nbconvert.ipynb"],
    )
    asser_value = "\'infractl   "
    assert asser_value in output, f"There is no {asser_value} in output: {output}"
