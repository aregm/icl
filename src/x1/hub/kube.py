"""Kubernetes utils."""

from __future__ import annotations

import os
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
        return client.CoreV1Api(api_client=self.api_client)


def api() -> KubeApi:
    """Returns default KubeApi object."""
    global DEFAULT_KUBE_API
    if DEFAULT_KUBE_API is None:
        DEFAULT_KUBE_API = KubeApi()
    return DEFAULT_KUBE_API
