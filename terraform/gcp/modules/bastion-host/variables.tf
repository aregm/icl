variable "bastion_name" {
  description = "Name of bastion host for SSH/RDP traffic"
  type = string
  default = "bastion-icl"
}

variable "bastion_machine_type" {
  description = "Machine type to use for bastion host"
  type = string
  default = "n1-standard-1"
}

variable "gcp_zone" {
  description = "Name of GKE zone"
  type = string
}

variable "bastion_public_key_content" {
  description = "Path to the SSH public key for the bastion host."
  type = string
}

variable "bastion_username" {
  description = "Username for the bastion host."
  type = string
  default = "bastion_user"
}

variable "bastion_tags" {
  description = "Tags associated with bastion host for applying firewall rules"
  type = list(string)
}