data "http" "nvidia-device-plugin" {
  url = "https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/${var.device-plugin-release}/nvidia-device-plugin.yml"
}

resource "local_file" "nvidia-device-plugin" {
  content  = data.http.nvidia-device-plugin.response_body
  filename = "/tmp/nvidia-device-plugin.yml"
}

resource "null_resource" "nvidia-device-plugin" {
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -f ${local_file.nvidia-device-plugin.filename}
    EOT
  }
}

resource "helm_release" "gpu-operator" {
  name = "gpu-operator"
  namespace = "gpu-operator"
  create_namespace = true
  version = var.gpu-operator-release
  repository = "https://helm.ngc.nvidia.com/nvidia/"
  chart = "gpu-operator"
}
