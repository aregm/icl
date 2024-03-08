variable "cluster_name" {
  description = "Name of GKE cluster"
  type = string
}

variable "gcp_project" {
  description = "Name of GKE project"
  type = string
}

#variable "gcp_region" {
#  description = "Name of GKE region"
#  type = string
#}

variable "gcp_zone" {
  description = "Name of GKE zone"
  type = string
}

variable "node_version" {
  description ="Kubernetes version to use for GKE"
  type = string
}

variable "machine_type" {
  description = "Machine type to use for GKE"
  type = string
}

variable "gpu_enabled" {
  description = "Enable GPU support"
  type = bool
  default = false
}

variable "gpu_model" {
  description = "Model of GPU to attach to nodes in pool"
  type = string
  default = "none"
}

variable "gke_gpu_driver_version" {
  description = "The NVIDIA driver version to install"
  default = "DEFAULT"
}