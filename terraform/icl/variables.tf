variable "namespace_labels" {
  description = "Labels for namespace"
  type = map(string)
  default = {}
}

variable "openshift_enabled" {
  description = "Enable using OpenShift services"
  type = bool
  default = false
}

variable "ceph_enabled" {
  description = "True if Ceph cluster is required"
  default = false
  type = bool
}

variable "ceph_device_filter" {
  description = "Regex for devices that are available for Ceph, for example '^sd.'"
  type = string
  default = ".*"
}

variable "ceph_devices" {
  description = "List of devices, for example [{name = /dev/loop0}]"
  type = list(map(string))
  default = []
}

variable "ceph_allow_loop_devices" {
  description = "If true, loop devices are allowed to be used for osds"
  type = bool
  default = false
}

variable "local_storage_enabled" {
  description = "True if local storage provisioner is required"
  default = false
  type = bool
}

variable "local_storage_disks" {
  description = "List of disks managed by local-storage-provisioner, for example ['sda']"
  type = list(string)
  default = []
}

variable "local_path_enabled" {
  description = "True if local path provisioner is required"
  default = true
  type = bool
}

variable "default_storage_class" {
  description = "Kubernetes storage class to use, 'local-path' or 'ceph-block'"
  default = "local-path"
  type = string
}

variable "prometheus_enabled" {
  description = "Enable Prometheus stack"
  type = bool
  default = false
}

variable "metrics_server_enabled" {
  description = "Enable metrics-server (https://github.com/kubernetes-sigs/metrics-server/)"
  type = bool
  default = false
}

variable "kubernetes_dashboard_enabled" {
  description = "Enable Kubernetes dashboard"
  type = bool
  default = true
}

variable "clearml_enabled" {
  description = "Enable ClearML https://github.com/allegroai/clearml"
  type = bool
  default = false
}

variable "cert_manager_enabled" {
  description = "Enable cert-manager"
  type = bool
  default = false
}

variable "ingress_domain" {
  description = "Ingress domain name"
  default = "localtest.me"
  type = string
}

variable "ingress_nginx_enabled" {
  description = "Enable ingress-nginx"
  type = bool
  default = true
}

variable "ingress_nginx_service_enabled" {
  description = "Enable LoadBalancer service for ingress-nginx (required for AWS)"
  type = bool
  default = false
}

variable "docker_registry_enabled" {
  description = "Enable docker-registry"
  type = bool
  default = true
}

variable "docker_registry_storage_size" {
  description = "Storage size for docker-registry"
  default = "512Mi"
  type = string
}

variable "prefect_image_tag" {
  description = "Tag of the official Prefect Docker image"
  default = "2.13.6-python3.9"
  type = string
}

variable "prefect_api_url" {
  description = "External URL for Prefect API to be used in UI, so it can communicate with the API from a web browser"
  default = ""
  type = string
}

variable "ray_image" {
  description = "Full tag for Ray Docker image"
  default = "pbchekin/icl-ray:2.6.1-py39"
  type = string
}

variable "ray_object_store" {
  description = "Size of Ray object store, bytes"
  default = 78643200 # minimum allowed is 75Mi
  type = number
}

variable "ray_worker_nodes" {
  description = "Number of Ray worker nodes"
  default = 0
  type = number
}

variable "ray_load_balancer_enabled" {
  description = "Enable LoadBalancer service on port 80 for Ray client endpoint"
  type = bool
  default = false
}

variable "dask_enabled" {
  description = "True if Dask cluster is required"
  default = false
  type = bool
}

variable "dask_workers" {
  description = "Number of Dask workers"
  default = 1
  type = number
}

variable "minio_enabled" {
  description = "Enable MinIO"
  default = true
  type = bool
}

variable "minio_ha_enabled" {
  description = "MinIO HA mode (true), or a single server mode (false)"
  default = false
  type = bool
}

variable "minio_servers" {
  description = "Number of MinIO servers in HA configuration"
  type = number
  default = 1
}

variable "jupyterhub_vscode_enabled" {
  description = "Enable JupyterHub for VS Code"
  type = bool
  default = false
}

variable "jupyterhub_pre_puller_enabled" {
  description = "Enable JupyterHub image pre-puller"
  default = true
  type = bool
}

variable "jupyterhub_singleuser_volume_size" {
  description = "Size of a persistent volume for a single user session"
  default = "2536Mi"
  type = string
}

variable "jupyterhub_singleuser_default_image" {
  description = "Default Docker image for JupyterHub default profile"
  # original image: jupyterhub/k8s-singleuser-sample:2.0.1-0.dev.git.6035.h643c0f0c
  default = "pbchekin/icl-jupyterhub:0.0.17"
  type = string
}

variable "jupyterhub_gpu_profile_image" {
  description = "Docker image for JupyterHub GPU profile"
  type = string
  default = "pbchekin/icl-jupyterhub-gpu:0.0.17"
}

variable "jupyterhub_cluster_admin_enabled" {
  description = "Enable admin access to Kubernetes cluster from JupyterHub sessions"
  type = bool
  default = false
}

variable "olm_enabled" {
  description = "Enable Operator Lifecycle Manager, see https://operatorhub.io/how-to-install-an-operator"
  type = bool
  default = false
}

variable "ovms_enabled" {
  description = "Enable OpenVINO Model Server, see https://operatorhub.io/operator/ovms-operator"
  type = bool
  default = false
}

variable "mpi_enabled" {
  description = "Enable MPI operator"
  type = bool
  default = false
}

variable "shared_volume_enabled" {
  description = "Enable shared volume"
  type = bool
  default = false
}

variable "shared_volume_size" {
  description = "Size of shared volume"
  type = string
  default = "1024Gi"
}

variable "shared_volume_storage_class" {
  description = "Storage class for shared volume"
  type = string
  default = "ceph-filesystem"
}

variable "ceph_secret_namespace" {
  description = "Ceph secret namespace"
  type = string
  default = "rook-ceph"
}

variable "externaldns_enabled" {
  description = "Enable ExternalDNS for the cluster"
  type = bool
  default = false
}

variable "nfd_enabled" {
  description = "Enable Node Feature Discovery"
  type = bool
  default = false
}

variable "intel_gpu_enabled" {
  description = "Enable Intel GPU support"
  type = bool
  default = false
}
