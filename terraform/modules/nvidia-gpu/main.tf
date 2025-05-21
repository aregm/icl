resource "helm_release" "gpu-operator" {
  name = "gpu-operator"
  namespace = "gpu-operator"
  create_namespace = true
  version = var.gpu-operator-release
  repository = "https://helm.ngc.nvidia.com/nvidia/"
  chart = "gpu-operator"
  atomic = true
  cleanup_on_fail = true
  reset_values = true
  replace = true
  values = [
    <<-EOT
    driver:
      enabled: false
      useHostMounts: true
    toolkit:
      enabled: true
      version: v1.15.0-ubuntu20.04
    devicePlugin:
      enabled: true
      version: v0.14.3-ubuntu20.04
    migManager:
      enabled: false
    EOT
  ]
}
