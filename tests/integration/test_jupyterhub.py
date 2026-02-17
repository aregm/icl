from conftest import copy_file_to_pod, exec_in_pod
from kubernetes import client, config

IPYNB_TEST_FILE_PATH = "data/test_notebook.ipynb"


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

    # In order to execute NB inside the python-3.12 conda environment, we install nbconvert to this "user" environment.
    # There is a better way to do this.
    exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            "/bin/bash",
            "-c",
            "{ ~/.conda/bin/conda install -n python-3.12 -y nbconvert && \
         ~/.conda/bin/conda run -n python-3.12 \
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
