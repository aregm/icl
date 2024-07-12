output "gpu_enabled" {
  value = var.gpu_enabled
  description = "Enables GPU support"
}

output "gpu_model" {
  value = var.gpu_model
  description = "Model of GPU to attach to nodes in pool"
}

output "gke_gpu_driver_version" {
  value = var.gke_gpu_driver_version
  description = "The NVIDIA driver version to install"
}
