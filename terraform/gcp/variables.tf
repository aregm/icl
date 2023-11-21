variable "cluster_name" {
  description = "Name of GKE cluster"
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

#variable "gcp_region" {
#  description = "Name of GKE region"
#  type = string
#}

variable "gcp_project" {
  description = "Name of GKE project"
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
