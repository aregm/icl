import time

import requests
from kubernetes import client, config, stream

IPYNB_TEST_FILE_PATH = "data/test_notebook.ipynb"


def exec_in_pod(api, pod_name, namespace, command):
    return stream.stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )


# https://github.com/kubernetes-client/python/issues/476#issuecomment-375056804
def copy_file_to_pod(api, pod_name, namespace, source_file, destination_file):
    exec_command = ['/bin/sh']
    resp = stream.stream(
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

    commands = [
        bytes(f"cat <<'EOF' >{destination_file}\n", 'utf-8'),
        buffer,
        bytes("EOF\n", 'utf-8'),
    ]

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


def test_jupyterhub_notebook(jupyterhub_namespace, jupyterhub_session_pod_name):
    """Uploads a Jupyter notebook and executes it in the JupyterHub session."""
    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    copy_file_to_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        IPYNB_TEST_FILE_PATH,  # relative to tests/integration
        "/tmp/test_notebook.ipynb",
    )

    # In order to execute NB inside the python-3.9 conda environment, we install nbconvert to this "user" environment.
    # There is a better way to do this.
    exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            "/bin/bash",
            "-c",
            "{ ~/.conda/bin/conda install -n python-3.9 -y nbconvert && \
         ~/.conda/bin/conda run -n python-3.9 \
            jupyter nbconvert /tmp/test_notebook.ipynb --execute --to notebook; } > /tmp/nbconvert.log 2>&1",
        ],
    )

    output = exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        ["/bin/cat", "/tmp/test_notebook.nbconvert.ipynb"],
    )
    assert 'infractl' in output, f"There is no 'infractl' in output: {output}"


def test_jupyterhub_enable_ssh(jupyterhub_namespace, jupyterhub_session_pod_name):
    """Enables ssh in the JupyterHub session."""
    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    _ = exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            '/bin/bash',
            '-c',
            'echo "jovyan:insecure" | sudo chpasswd',
        ],
    )

    output = exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            '/bin/bash',
            # Specify -l (login) option to execute ~/.profile and set conda environment
            '-lc',
            'infractl ssh enable',
        ],
    )

    assert 'log in to your session' in output
