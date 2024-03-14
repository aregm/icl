variable "cluster_name" {
  description = "Name of GKE cluster"
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
  description = "Enables GPU support"
  type = bool
  default = false
}

variable "gpu_model" {
  description = "Model of GPU to attach to nodes in pool"
  type = string
  default = "none"
}

variable "gke_gpu_driver_version" {
  default = "DEFAULT"
  description = "The NVIDIA driver version to install"
}

variable "node_count" {
  default = 1
  type = number
  description = "Number of nodes in the pool"
}
variable "gpu_count" {
  default = 1
  type = number
  description = "Number of GPUs in the node pool"
}

variable "shared_gpu" {
  description = "Enable more than one container per GPU"
  type = bool
  default = true
}