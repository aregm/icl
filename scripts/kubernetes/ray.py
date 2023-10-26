#!/usr/bin/env python3

"""Script to update Ray cluster with the new image for the head and worker nodes."""

import sys
from typing import Dict

from kubernetes import client, config


def get_ray_cluster():
    """Gets Ray cluster."""
    with client.ApiClient() as api_client:
        api_instance = client.CustomObjectsApi(api_client)
        return api_instance.get_namespaced_custom_object(
            group='ray.io',
            plural='rayclusters',
            version='v1alpha1',
            namespace='ray',
            name='ray',
        )


def get_ray_cluster_images() -> Dict[str, str]:
    """Prints Ray cluster images for the head and worker nodes."""
    response = get_ray_cluster()
    container = response['spec']['headGroupSpec']['template']['spec']['containers'][0]
    images = {'headGroupSpec': container['image']}
    for worker_group_spec in response['spec']['workerGroupSpecs']:
        container = worker_group_spec['template']['spec']['containers'][0]
        images[worker_group_spec['groupName']] = container['image']
    return images


def update_ray_cluster_image(image: str):
    """Updates Ray cluster with the new image for the head and worker nodes."""
    with client.ApiClient() as api_client:
        api_instance = client.CustomObjectsApi(api_client)

        response = get_ray_cluster()
        response['spec']['headGroupSpec']['template']['spec']['containers'][0]['image'] = image
        for worker_group_spec in response['spec']['workerGroupSpecs']:
            worker_group_spec['template']['spec']['containers'][0]['image'] = image

        api_instance.patch_namespaced_custom_object(
            group='ray.io',
            plural='rayclusters',
            version='v1alpha1',
            namespace='ray',
            name='ray',
            body={
                'spec': response['spec'],
            },
        )


def restart_ray_nodes():
    """Restarts Ray  nodes."""
    core_v1 = client.CoreV1Api()
    response = core_v1.list_namespaced_pod(namespace='ray', label_selector='ray.io/is-ray-node=yes')
    for pod in response.items:
        name = pod.metadata.name
        core_v1.delete_namespaced_pod(name=name, namespace='ray', grace_period_seconds=10)
        print(f'Deleted pod {name}')


if __name__ == '__main__':

    config.load_kube_config()
    print('Before', get_ray_cluster_images())
    update_ray_cluster_image(sys.argv[1])
    print('After ', get_ray_cluster_images())
    restart_ray_nodes()
