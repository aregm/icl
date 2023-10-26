resource "null_resource" "nfd_gpu_rules" {
  count = var.shared_gpu ? 1 : 0
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -k https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/nfd/overlays/node-feature-rules?ref=${var.release}
    EOT
  }

  triggers = {
    release = var.release
  }
}

# shared mode, 30 containers per GPU
# https://github.com/intel/intel-device-plugins-for-kubernetes/blob/main/cmd/gpu_plugin/README.md#install-to-nodes-with-nfd-monitoring-and-shared-dev
resource "null_resource" "gpu_plugin_shared" {
  count = var.shared_gpu ? 1 : 0
  depends_on = [null_resource.nfd_gpu_rules]
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -k https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/gpu_plugin/overlays/monitoring_shared-dev_nfd?ref=${var.release}
    EOT
  }

  triggers = {
    release = var.release
  }
}

# exclusive mode, 1 container per GPU
# https://github.com/intel/intel-device-plugins-for-kubernetes/blob/main/cmd/gpu_plugin/README.md#install-to-nodes-with-intel-gpus-with-nfd
resource "null_resource" "gpu_plugin_exclusive" {
  count = var.shared_gpu ? 0 : 1
  depends_on = [null_resource.nfd_gpu_rules]
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -k https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/gpu_plugin/overlays/nfd_labeled_nodes?ref=${var.release}
    EOT
  }

  triggers = {
    release = var.release
  }
}
