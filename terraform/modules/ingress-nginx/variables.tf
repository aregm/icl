variable "ingress_nginx_service_enabled" {
  description = "Enable LoadBalancer service for ingress-nginx (required for AWS)"
  type = bool
  default = false
}

variable "ingress_nginx_http_port" {
  description = "HTTP host port"
  type = number
  default = 80
}

variable "ingress_nginx_https_port" {
  description = "HTTPS host port"
  type = number
  default = 443
}
