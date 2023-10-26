variable "release" {
  description = "Version of Ceph operator"
  default = "v1.12.2"
  type = string
}

variable "ingress_domain" {
  description = "Ingress domain name"
  default = "localtest.me"
  type = string
}

variable "ceph_device_filter" {
  description = "Regex for devices that are available for Ceph, for example '^sd.'"
  type = string
  default = ".*"
}

variable "ceph_devices" {
  description = "List of devices, for example [{name = /dev/loop0}], if set then ceph_device_filter is not used"
  type = list(map(string))
  default = []
}

variable "ceph_allow_loop_devices" {
  description = "If true, loop devices are allowed to be used for osds"
  type = bool
  default = false
}
