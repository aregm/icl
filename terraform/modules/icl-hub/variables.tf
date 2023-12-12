variable "namespace_labels" {
  description = "Labels for namespace"
  type = map(string)
  default = {}
}

variable "ingress_domain" {
  description = "Ingress domain name"
  type = string
}

variable "use_node_ip_for_user_ports" {
  description = "Use k8s Node's IP address when exposing user ports"
  type = bool
}

variable "use_external_node_ip_for_user_ports" {
  description = "Use k8s Node's ExternalIP address when exposing user ports (use with use_node_ip_for_user_ports)"
  type = bool
}
