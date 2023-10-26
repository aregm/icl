variable "namespace_labels" {
  description = "Labels for namespace"
  type = map(string)
  default = {}
}

variable "ingress_domain" {
  description = "Ingress domain name"
  type = string
}
