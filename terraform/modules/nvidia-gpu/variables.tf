variable "gpu-operator-release" {
  description = "Version of NVIDIA GPU Operator"
  default = "v23.9.0"
  type = string
}

variable "device-plugin-release" {
  description = "Version of NVIDIA Device Plugin"
  default = "v0.15.0-rc.2"
}
