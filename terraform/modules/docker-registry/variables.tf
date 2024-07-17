variable "release" {
  description = "Version of docker-registry Helm chart"
  default = "2.2.3"
  type = string
}

variable "storage_class" {
  description = "Storage class for docker-registry volume"
  type = string
}

variable "storage_size" {
  description = "Storage cize for docker-registry volume"
  type = string
}

variable "ingress_domain" {
  description = "Ingress domain name"
  type = string
}
