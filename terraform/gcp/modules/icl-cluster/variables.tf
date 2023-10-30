variable "cluster_name" {
  description = "Name of GKE cluster"
  type = string
}

variable "node_version" {
  description ="Kubernetes version to use for GKE"
  type = string
}
