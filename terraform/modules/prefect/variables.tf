variable "namespace_labels" {
  description = "Labels for namespace"
  type = map(string)
  default = {}
}

variable "worker_namespace" {
  description = "Namespace for Prefect worker"
  type = string
  default = "default"
}

variable "chart_version" {
  description = "Version of Prefect Helm chart"
  default = "2026.2.12200748"
  type = string
}

variable "server_image_tag" {
  description = "Tag of the Prefect server Docker image"
  type = string
  default = "3.6.17-python3.11"
}

variable "worker_image_tag" {
  description = "Tag of the Prefect worker Docker image"
  type = string
  default = "3-python3.11-kubernetes"
}

variable "work_pool_name" {
  description = "Name of the Prefect work pool for the worker"
  type = string
  default = "default-pool"
}

variable "api_url" {
  description = "External URL for Prefect API to be used in UI, so it can communicate with the API from a web browser"
  type = string
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
