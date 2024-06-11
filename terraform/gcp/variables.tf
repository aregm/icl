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

variable "shared_gpu" {
  description = "Enable more than one container per GPU"
  type = bool
  default = true
}

variable "create_bastion" {
  description = "Boolean to determine if bastion host is required"
  type = bool
  default = false
}

variable "bastion_name" {
  description = "Name of bastion host for SSH/RDP traffic"
  type = string
  default = "bastion"
}

variable "bastion_username" {
  description = "Username to be created on bastion host"
  type = string
}

variable "bastion_machine_type" {
  description = "Machine type to use for bastion host"
  type = string
  default = "n1-standard-1"
}

variable "bastion_public_key_content" {
  description = "Public key string for connection to bastion host"
  type = string
}

variable "bastion_source_ranges" {
  description = "List of IP ranges to allow access to bastion host"
  type = list(string)
}