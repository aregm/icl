variable "release" {
  description = "Release of Intel Device Plugins for Kubernetes (https://github.com/intel/intel-device-plugins-for-kubernetes/releases)"
  type = string
  default = "v0.27.1"
}

variable "shared_gpu" {
  description = "Enable more than one container per GPU"
  type = bool
  default = true
}
