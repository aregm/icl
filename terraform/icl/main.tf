# KUBE_CONFIG_PATH must be set to, for example, ~/.kube/config
provider "kubernetes" {
}

# KUBE_CONFIG_PATH must be set to, for example, ~/.kube/config
provider "helm" {
  kubernetes {
  }
}

terraform {
  backend "kubernetes" {
    secret_suffix = "icl"
    namespace = "kube-system"
  }
}

module "ceph" {
  count = var.ceph_enabled ? 1 : 0
  source = "../modules/ceph"
  ingress_domain = var.ingress_domain
  ceph_device_filter = var.ceph_device_filter
  ceph_allow_loop_devices = var.ceph_allow_loop_devices
  ceph_devices = var.ceph_devices
}

module "local-path-provisioner" {
  count = var.local_path_enabled ? 1 : 0
  source = "../modules/local-path-provisioner"
}

module "local-storage-provisioner" {
  count = var.local_storage_enabled ? 1 : 0
  source = "../modules/local-storage-provisioner"
  local_storage_disks = var.local_storage_disks
}

module "ingress-nginx" {
  count = var.ingress_nginx_enabled ? 1 : 0
  source = "../modules/ingress-nginx"
  ingress_nginx_service_enabled = var.ingress_nginx_service_enabled
}

module "prometheus" {
  count = var.prometheus_enabled ? 1 : 0
  source = "../modules/prometheus"
  metrics_server_enabled = var.metrics_server_enabled
  ingress_domain = var.ingress_domain
  storage_class = var.default_storage_class
}

module "xpumanager" {
  count = var.prometheus_enabled && var.gpu_type == "intel" ? 1 : 0
  depends_on = [module.prometheus]
  source = "../modules/xpumanager"
}

module "docker-registry" {
  count = var.docker_registry_enabled ? 1 : 0
  source = "../modules/docker-registry"
  storage_class = var.default_storage_class
  storage_size = var.docker_registry_storage_size
  ingress_domain = var.ingress_domain
}

module "kubernetes-dashboard" {
  count = var.kubernetes_dashboard_enabled ? 1 : 0
  source = "../modules/kubernetes-dashboard"
  ingress_domain = var.ingress_domain
}

module "externaldns" {
  count = var.externaldns_enabled ? 1 : 0
  source = "../modules/externaldns"
}

module "prefect" {
  source = "../modules/prefect"
  depends_on = [module.shared-volume]
  namespace_labels = var.namespace_labels
  image_tag = var.prefect_image_tag
  api_url = var.prefect_api_url
  ingress_domain = var.ingress_domain
  shared_volume_enabled = var.shared_volume_enabled
}

module "ray" {
  count = var.ray_enabled ? 1 : 0
  source = "../modules/ray"
  depends_on = [module.shared-volume]
  namespace_labels = var.namespace_labels
  ray_image = var.ray_image
  ray_object_store = var.ray_object_store
  ray_worker_nodes = var.ray_worker_nodes
  ray_load_balancer_enabled = var.ray_load_balancer_enabled
  ingress_domain = var.ingress_domain
  shared_volume_enabled = var.shared_volume_enabled
}

module "dask" {
  count = var.dask_enabled ? 1 : 0
  source = "../modules/dask"
  dask_workers = var.dask_workers
  ingress_domain = var.ingress_domain
}

module "minio" {
  count = var.minio_enabled ? 1 : 0
  source = "../modules/minio"
  minio_ha_enabled = var.minio_ha_enabled
  default_storage_class = var.default_storage_class
  ingress_domain = var.ingress_domain
  minio_servers = var.minio_servers
}

module "jupyterhub" {
  source = "../modules/jupyterhub"
  depends_on = [module.shared-volume]
  namespace_labels = var.namespace_labels
  default_storage_class = var.default_storage_class
  jupyterhub_pre_puller_enabled = var.jupyterhub_pre_puller_enabled
  jupyterhub_singleuser_volume_size = var.jupyterhub_singleuser_volume_size
  jupyterhub_singleuser_default_image = var.jupyterhub_singleuser_default_image
  jupyterhub_gpu_profile_enabled = var.gpu_enabled
  jupyterhub_shared_memory_size = var.jupyterhub_shared_memory_size
  jupyterhub_gpu_profile_image = var.gpu_enabled ? (var.gpu_type == "intel" ? var.jupyterhub_intel_gpu_profile_image : var.jupyterhub_nvidia_gpu_profile_image) : null
  jupyterhub_profiles = var.jupyterhub_profiles
  ingress_domain = var.ingress_domain
  shared_volume_enabled = var.shared_volume_enabled
  jupyterhub_extra_resource_limits = var.jupyterhub_extra_resource_limits
  jupyterhub_cluster_admin_enabled = var.jupyterhub_cluster_admin_enabled
}

module "jupyterhub-vscode" {
  count = var.jupyterhub_vscode_enabled ? 1 : 0
  source = "../modules/jupyterhub-vscode"
  depends_on = [module.shared-volume]
  namespace_labels = var.namespace_labels
  default_storage_class = var.default_storage_class
  jupyterhub_pre_puller_enabled = var.jupyterhub_pre_puller_enabled
  jupyterhub_singleuser_volume_size = var.jupyterhub_singleuser_volume_size
  ingress_domain = var.ingress_domain
  shared_volume_enabled = var.shared_volume_enabled
}

module "clearml" {
  count = var.clearml_enabled ? 1 : 0
  source = "../modules/clearml"
  ingress_domain = var.ingress_domain
}

module "cert-manager" {
  count = var.cert_manager_enabled ? 1 : 0
  source = "../modules/cert-manager"
  ingress_domain = var.ingress_domain
}

module "olm" {
  count = var.olm_enabled ? 1 : 0
  source = "../modules/olm"
}

module "ovms" {
  depends_on = [module.olm]
  count = var.ovms_enabled ? 1 : 0
  source = "../modules/ovms"
  openshift_enabled = var.openshift_enabled
}

module "mpi" {
  count = var.mpi_enabled ? 1 : 0
  source = "../modules/mpi"
  namespace_labels = var.namespace_labels
}

module "shared-volume" {
  depends_on = [module.ceph]
  count = var.shared_volume_enabled ? 1 : 0
  source = "../modules/shared-volume"
  namespace_labels = var.namespace_labels
  shared_volume_size = var.shared_volume_size
  shared_volume_storage_class = var.shared_volume_storage_class
  ceph_secret_namespace = var.ceph_secret_namespace
}

module "nfd" {
  count = var.nfd_enabled ? 1 : 0
  source = "../modules/nfd"
}

module "intel-gpu" {
  depends_on = [module.nfd]
  count = var.gpu_type == "intel" ? 1 : 0
  source = "../modules/intel-gpu"
}

module "nvidia-gpu" {
  count = (var.gpu_type == "nvidia" && var.enable_nvidia_operator == true) ? 1 : 0
  source = "../modules/nvidia-gpu"
}

module "icl-hub" {
  source = "../modules/icl-hub"
  namespace_labels = var.namespace_labels
  ingress_domain = var.ingress_domain
  use_node_ip_for_user_ports = var.use_node_ip_for_user_ports
  use_external_node_ip_for_user_ports = var.use_external_node_ip_for_user_ports
}
