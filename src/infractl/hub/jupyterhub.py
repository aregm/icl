"""icl-hub JupyterHub commands."""

import base64
import logging
import subprocess
import sys
from typing import Callable, List, Optional, Union

import click
from kubernetes import client, stream

import infractl.kubernetes as kube
from infractl.hub import config, root

JUPYTERHUB_NAMESPACE = 'jupyterhub'
ICL_HUB_NAMESPACE = 'icl-hub'


@root.cli.group()
def jupyterhub():
    """Manage JupyterHub."""


@jupyterhub.command('list-sessions')
def list_sessions_cmd():
    """List user sessions and names."""
    for pod in get_user_pods(JUPYTERHUB_NAMESPACE):
        print(
            pod.metadata.name,
            pod.metadata.annotations.get('hub.jupyter.org/username'),
        )


@jupyterhub.command('list-users')
def list_users_cmd():
    """List JupyterHub users."""
    users = list_users()
    if users:
        print('\n'.join(users))


@jupyterhub.group()
def ssh():
    """Manage SSH access to JupyterHub session."""


@ssh.command('enable')
@click.argument('username')
@click.option('--key', help='Public SSH key')
def enable_ssh_cmd(username: str, key: Optional[str] = None):
    """Enable ssh to JupyterHub session."""
    print(enable_ssh(username, key))


@ssh.command('disable')
@click.argument('username')
def disable_ssh_cmd(username: str):
    """Disable ssh to JupyterHub session."""
    disable_ssh(username)


ResponseCallback = Callable[[str], None]


class JupyterHubError(Exception):
    """JupyterHub error."""


def _stdout_callback(line: str):
    """Callback for printing a line on stdout."""
    print(line)


def _stderr_callback(line: str):
    """Callback for printing a line on stderr."""
    print(line, file=sys.stderr)


def execute_in_pod(
    *,
    pod: str,
    container: Optional[str] = None,
    namespace: Optional[str] = None,
    command: Union[str, List[str]],
    stdout_callback: ResponseCallback = _stdout_callback,
    stderr_callback: ResponseCallback = _stderr_callback,
    check: bool = True,
):
    """Execute a command in pod."""
    if isinstance(command, str):
        command = ['/bin/bash', '-c', command]
    response = stream.stream(
        kube.api().core_v1().connect_get_namespaced_pod_exec,
        pod,
        namespace or JUPYTERHUB_NAMESPACE,
        container=container,
        command=command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
    while response.is_open():
        response.update()
        if response.peek_stderr():
            stderr_callback(response.readline_stderr())
        if response.peek_stdout():
            stdout_callback(response.readline_stdout())
    if check and response.returncode != 0:
        raise JupyterHubError(f'Process returned {response.returncode}')


def execute_in_pod_with_logger(logger: logging.Logger, **kwargs):
    """Execute a command in pod and send stderr/stdout to logger."""

    def logger_out(line: str):
        """Log the line with info."""
        logger.info(line)

    def logger_err(line: str):
        """Log the line with error."""
        logger.error(line)

    kwargs['stdout_callback'] = logger_out
    kwargs['stderr_callback'] = logger_err
    execute_in_pod(**kwargs)


def get_user_pod(username: str) -> Optional[client.V1Pod]:
    """Returns user pod."""
    for pod in get_user_pods(JUPYTERHUB_NAMESPACE):
        if pod.metadata.annotations.get('hub.jupyter.org/username') == username:
            return pod
    return None


def get_user_pods(namespace: str) -> List[client.V1Pod]:
    """Returns a list of pods with JupyterHub user sessions."""
    response = (
        kube.api()
        .core_v1()
        .list_namespaced_pod(
            namespace=namespace,
            label_selector='component=singleuser-server',
        )
    )
    return response.items


def get_hub_pod(namespace: str) -> client.V1Pod:
    """Returns JupyterHub pod."""
    response = (
        kube.api()
        .core_v1()
        .list_namespaced_pod(
            namespace=namespace,
            label_selector='component=hub',
        )
    )
    return response.items[0]


def get_node_ip(name: str, external: bool = False) -> str:
    """Returns node IP address."""
    external_ip = None
    internal_ip = None

    response = kube.api().core_v1().read_node_status(name)
    for address in response.status.addresses:
        if address.type == 'ExternalIP':
            external_ip = address.address
        if address.type == 'InternalIP':
            internal_ip = address.address
    if external_ip and external:
        return external_ip
    return internal_ip or name


def get_user_id(username: str) -> str:
    """Returns user id."""
    hub_pod = get_hub_pod(JUPYTERHUB_NAMESPACE)
    response = stream.stream(
        kube.api().core_v1().connect_get_namespaced_pod_exec,
        hub_pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        command=[
            'sqlite3',
            '-readonly',
            'jupyterhub.sqlite',
            f'.param set :username "{username}"',
            'select id from users where name=:username;',
        ],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    return response.strip()


def list_users() -> List[str]:
    """List JupyterHub users."""
    hub_pod = get_hub_pod(JUPYTERHUB_NAMESPACE)
    # TODO: implement a helper method to execute scripts in pod
    response = stream.stream(
        kube.api().core_v1().connect_get_namespaced_pod_exec,
        hub_pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        command=['sqlite3', '-readonly', 'jupyterhub.sqlite', 'select id, name from users;'],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
    response.run_forever()
    if response.returncode != 0:
        raise Exception(response.read_stderr())
    return response.read_stdout().strip().splitlines()


def _enable_ssh_script() -> str:
    """Returns Bash script to enable ssh in JupyterHub session."""
    return """
        sudo chown jovyan:jovyan /home/jovyan
        sudo chmod 00700 /home/jovyan
        if [[ -f /run/sshd.pid && -d /proc/$(cat /run/sshd.pid) ]]; then
            echo sshd is running
        else
            if [[ -x /usr/sbin/sshd ]]; then
                echo sshd is installed
            else
                echo ssh is not installed, trying to install ...
                export DEBIAN_FRONTEND=noninteractive
                sudo -E apt-get update
                sudo -E apt-get install -y --no-install-recommends openssh-server
            fi
            echo starting sshd ...
            sudo mkdir -p -m0755 /var/run/sshd
            sudo /usr/sbin/sshd
            echo sshd is running
        fi
    """


def _add_ssh_key_script(key: str):
    """Adds ssh key."""
    return f"""
        sudo chown jovyan:jovyan /home/jovyan
        mkdir -p ~/.ssh
        echo "{key}" >> ~/.ssh/authorized_keys
        cat ~/.ssh/authorized_keys | sort | uniq > ~/.ssh/authorized_keys.tmp
        mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys
        chmod 00600 ~/.ssh/authorized_keys
        sudo chmod 00700 /home/jovyan /home/jovyan/.ssh
    """


def _add_private_ssh_key_script(name: str, key: str):
    """Add private ssh key."""
    return f"""
        mkdir -p -m0700 ~/.ssh
        echo "{key}" > ~/.ssh/{name}
        chmod 0600 ~/.ssh/{name}
    """


def _add_jumphost_ssh_key(user_key: str, jumphost_key: str, host: str, port: int = 22):
    """Adds public ssh key to jumphost."""
    subprocess.check_output(
        ['/bin/bash', '-c', _add_private_ssh_key_script('jumphost', jumphost_key)]
    )
    subprocess.check_output(
        [
            '/usr/bin/ssh',
            '-o',
            'UserKnownHostsFile=/dev/null',
            '-o',
            'StrictHostKeyChecking=no',
            '-i',
            '~/.ssh/jumphost',
            '-p',
            port,
            host,
            f'/bin/bash -c {_add_ssh_key_script(user_key)}',
        ]
    )


def enable_ssh(username: str, key: Optional[str] = None) -> str:
    """Enable ssh to JupyterHub session.

    Returns:
        ssh connection string
    """

    # Steps:
    # * Install sshd in the session container and start it in background.
    # * Add public ssh key to ~/.ssh/authorized keys.
    # * Create a Kubernetes NodePort service for ssh port.
    # * Optional: Add public ssh key to the tunnel user.

    # Modes to access NodePort:
    # * Direct
    # * SSH jumphost
    # * SSH proxy

    user_id = get_user_id(username)
    if not user_id:
        raise click.ClickException(f'No such JupyterHub user {username}')
    node_port = int(f'32{user_id.zfill(3)}')

    pod = get_user_pod(username)
    if not pod:
        raise click.ClickException(f'No JupyterHub session for user {username}')

    script = _enable_ssh_script()
    if key:
        script += _add_ssh_key_script(key)

    response = stream.stream(
        kube.api().core_v1().connect_get_namespaced_pod_exec,
        pod.metadata.name,
        JUPYTERHUB_NAMESPACE,
        container='notebook',
        command=['/bin/bash', '-ce', script],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    print(response)

    service_name = f'{pod.metadata.name}-ssh'
    service_body = client.V1Service(
        api_version='v1',
        kind='Service',
        metadata=client.V1ObjectMeta(
            name=service_name,
        ),
        spec=client.V1ServiceSpec(
            type='NodePort',
            selector={
                'hub.jupyter.org/username': pod.metadata.labels['hub.jupyter.org/username'],
                'component': 'singleuser-server',
            },
            ports=[
                client.V1ServicePort(
                    name='ssh',
                    port=22,
                    target_port=22,
                    node_port=node_port,
                    protocol='TCP',
                ),
            ],
        ),
    )

    try:
        kube.api().core_v1().read_namespaced_service(service_name, JUPYTERHUB_NAMESPACE)
    except client.exceptions.ApiException as error:
        if error.status == 404:
            kube.api().core_v1().create_namespaced_service(JUPYTERHUB_NAMESPACE, body=service_body)
        else:
            raise error

    response = kube.api().core_v1().read_namespaced_service(service_name, JUPYTERHUB_NAMESPACE)

    jumphost: str = ''
    if key:
        # if secret ssh-tunnel exists, use it to ssh to the tunnel and add user key
        try:
            response = (
                kube.api().core_v1().read_namespaced_secret('ssh-jumphost', ICL_HUB_NAMESPACE)
            )
            jumphost = base64.b64decode(response.data['host']).decode('utf-8')
            jumphost_key = base64.b64decode(response.data['key']).decode('utf-8')
            _add_jumphost_ssh_key(
                user_key=key,
                jumphost_key=jumphost_key,
                host=jumphost,
            )
        except client.exceptions.ApiException as error:
            if error.status != 404:
                raise error

    use_node_ip_for_user_ports = config.get().get('use_node_ip_for_user_ports')
    use_external_node_ip_for_user_ports = config.get().get('use_external_node_ip_for_user_ports')
    ingress_domain = config.get().get('ingress_domain')
    print('ingress_domain', ingress_domain)
    ssh_host = (
        get_node_ip(pod.spec.node_name, external=use_external_node_ip_for_user_ports)
        if use_node_ip_for_user_ports
        else ingress_domain
    )
    ssh_args = f'jovyan@{ssh_host} -p {response.spec.ports[0].node_port}'
    if jumphost:
        return f'ssh -J {jumphost} {ssh_args}'
    else:
        return f'ssh {ssh_args}'


def disable_ssh(username: str):
    """Disable ssh to JupyterHub session."""

    # Steps:
    # * TODO: Stop ssh in session container
    # * Delete service

    pod = get_user_pod(username)
    if not pod:
        raise click.ClickException(f'No JupyterHub session for user {username}')

    name = f'{pod.metadata.name}-ssh'
    try:
        kube.api().core_v1().delete_namespaced_service(name, JUPYTERHUB_NAMESPACE)
    except client.exceptions.ApiException as error:
        if error.status != 404:
            raise error
