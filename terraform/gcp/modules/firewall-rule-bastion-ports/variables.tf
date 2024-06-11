variable "bastion_source_ranges" {
  description = "List of IP ranges to allow access to bastion host"
  type = list(string)
}