variable "bastion_source_ranges" {
  description = "List of IP ranges to allow access to bastion host"
  type = list(string)
}

variable "bastion_tags" {
  description = "Tags for creating firewall rules and specifying the which bastion"
  type = list(string)
}

variable "cluster_tags" {
  description = "Tags for creating firewall rules and specifying target clusters"
  type = list(string)
}

variable "ssh_rule_name" {
  description = "User specific name for allow SSH firewall rule"
  type = string
}

variable "internal_rule_name" {
  description = "Tags for creating firewall rules and specifying target clusters"
  type = string
}
