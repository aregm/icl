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

variable "image" {
  description = "icl-hub image"
  type = string
  default = "pbchekin/icl-hub:0.0.4"
}

variable "ssh_host" {
  description = "Host name returned in the ssh command for JupyterHub sessions (default: ingress_domain)"
  type = string
  default = ""
}
