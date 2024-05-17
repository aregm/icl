variable "cluster_name" {
  description = "Name of EKS cluster"
  type = string
}

variable "cluster_version" {
  description = "Version of Kubernetes to use for EKS"
  type = string
}

variable "instance_type" {
  description = "AWS EC2 instance type to use for the cluster"
  type = string
}

variable "gpu_type" {
  description = "GPU type to use for the cluster"
  type = string
}

variable "vpc_id" {
  description = "VPC ID for EKS cluster"
  type = string
}

variable "subnet_ids" {
  description = "Subnet IDs for EKS cluster"
  type = list(string)
}
