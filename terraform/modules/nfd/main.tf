resource "null_resource" "repository" {
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -k https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/nfd?ref=${var.release}
    EOT
  }

  triggers = {
    release = var.release
  }
}
