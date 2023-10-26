#!/usr/bin/env python3

"""Script to update JupyterHub profile image."""

import base64
import sys
from typing import Optional

import yaml
from kubernetes import client, config


def get_hub_config():
    """Gets JupyterHub config."""
    core_v1 = client.CoreV1Api()
    data = core_v1.read_namespaced_secret(name='hub', namespace='jupyterhub').data
    return yaml.safe_load(base64.b64decode(data['values.yaml']))


def get_hub_profile_image(name: str) -> Optional[str]:
    """Gets JupyterHub profile image."""
    values = get_hub_config()
    for profile in values['singleuser']['profileList']:
        if profile['display_name'] == name:
            return profile['kubespawner_override']['image']
    return None


def update_hub_profile_image(name: str, image: str):
    """Updates JupyterHub profile image."""
    values = get_hub_config()
    core_v1 = client.CoreV1Api()
    for profile in values['singleuser']['profileList']:
        if profile['display_name'] == name:
            profile['kubespawner_override']['image'] = image
            break
    core_v1.patch_namespaced_secret(
        name='hub',
        namespace='jupyterhub',
        body={
            'data': {
                'values.yaml': base64.b64encode(yaml.dump(values).encode('utf-8')).decode('utf-8'),
            }
        },
    )


def restart_hub(old_image: Optional[str] = None):
    """Restarts JupyterHub hub."""
    core_v1 = client.CoreV1Api()

    # Delete hub pod
    response = core_v1.list_namespaced_pod(namespace='jupyterhub', label_selector='component=hub')
    for pod in response.items:
        name = pod.metadata.name
        core_v1.delete_namespaced_pod(name=name, namespace='jupyterhub', grace_period_seconds=10)
        print(f'Deleted pod {name}')

    response = core_v1.list_namespaced_pod(namespace='jupyterhub')
    for pod in response.items:
        for container in pod.spec.containers:
            if container.image == old_image:
                print(f'Deleted pod {pod.metadata.name}')
                # Do not actually delete now, just print the pod name
                # core_v1.delete_namespaced_pod(
                #     name=pod.metadata.name,
                #     namespace='jupyterhub',
                #     grace_period_seconds=10,
                # )
                break


def main(image: str):
    """Main function."""
    config.load_kube_config()
    old_image = get_hub_profile_image('X1')
    print('Before', old_image)
    update_hub_profile_image('X1', image)
    print('After ', get_hub_profile_image('X1'))
    restart_hub(old_image)


if __name__ == '__main__':
    main(sys.argv[1])
