"""Kubernetes utils."""

from __future__ import annotations

import os
import time
from typing import Optional

from kubernetes import client, config

DEFAULT_KUBE_API: Optional[KubeApi] = None


class KubeApi:
    """Wrapper for Kubernetes client.

    TODO: handle caching and re-authentication.
    """

    def __init__(self):
        if 'KUBERNETES_SERVICE_HOST' in os.environ and 'KUBERNETES_SERVICE_PORT' in os.environ:
            config.load_incluster_config()
            self.configuration = client.Configuration.get_default_copy()
        else:
            self.configuration = client.Configuration()
            config.load_kube_config(client_configuration=self.configuration)
        self.api_client = client.ApiClient(configuration=self.configuration)

    def core_v1(self) -> client.CoreV1Api:
        """Returns Kubernetes CoreV1Api client."""
        return client.CoreV1Api(api_client=self.api_client)

    def batch_v1(self) -> client.BatchV1Api:
        """Returns Kubernetes BatchV1Api client."""
        return client.BatchV1Api(api_client=self.api_client)

    def recreate_secret(self, namespace: str, body: client.V1Secret) -> client.V1Secret:
        """Recreates Kubernetes secret."""
        name = body.metadata.name
        try:
            self.core_v1().delete_namespaced_secret(name, namespace)
        except client.exceptions.ApiException as error:
            if error.status != 404:
                raise error
        return self.core_v1().create_namespaced_secret(namespace, body=body)

    def recreate_job(self, namespace: str, body: client.V1Job) -> client.V1Job:
        """Recreates Kubernetes job."""
        name = body.metadata.name
        # retry deleting the job to avoid HTTP 409 Conflict, object is being deleted
        for retries_left in reversed(range(5)):
            try:
                self.batch_v1().delete_namespaced_job(
                    name,
                    namespace,
                    propagation_policy='Foreground',
                )
            except client.exceptions.ApiException as error:
                if error.status == 404:
                    break
                elif retries_left == 0:
                    raise error
            time.sleep(1)
        return self.batch_v1().create_namespaced_job(namespace, body=body)


def api() -> KubeApi:
    """Returns default KubeApi object."""
    global DEFAULT_KUBE_API
    if DEFAULT_KUBE_API is None:
        DEFAULT_KUBE_API = KubeApi()
    return DEFAULT_KUBE_API
