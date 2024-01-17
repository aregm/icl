variable "namespace_labels" {
  description = "Labels for namespace"
  type = map(string)
  default = {}
}

variable "default_storage_class" {
  description = "Kubernetes storage class"
  type = string
}

variable "jupyterhub_pre_puller_enabled" {
  description = "Enable JupyterHub image pre-puller"
  type = bool
}

variable "jupyterhub_singleuser_volume_size" {
  description = "Size of a persistent volume for a single user session"
  type = string
}

variable "jupyterhub_singleuser_default_image" {
  description = "Default Docker image for JupyterHub default profile"
  type = string
}

variable "jupyterhub_gpu_profile_enabled" {
  description = "Enable JupyterHub GPU profile"
  type = bool
  default = false
}

variable "jupyterhub_gpu_profile_image" {
  description = "Docker image for JupyterHub GPU profile"
  type = string
  default = ""
}

variable "jupyterhub_shared_memory_size" {
  description = "Custom size of /dev/shm, empty for default"
  type = string
  default = ""
}

variable "prefect_api_url" {
  description = "Prefect API URL"
  type = string
  default = "http://prefect-server.prefect:4200/api"
}

variable "ingress_domain" {
  description = "Ingress domain name"
  default = "localtest.me"
  type = string
}

variable "shared_volume_enabled" {
  description = "Enable shared volume"
  type = bool
  default = false
}

variable "jupyterhub_cluster_admin_enabled" {
  description = "Enable admin access to Kubernetes cluster from JupyterHub sessions"
  type = bool
  default = false
}
