output "gpu_enabled" {
  value       = var.gpu_enabled
  description = "Is a GPU installed in cluster nodes?"
}

output "gpu_type" {
  value       = var.gpu_type
  description = "Used to set kubespawner settings for amd/intel/nvidia GPUs and select correct images for deployment"
}

output "jupyterhub_gpu_profile_image" {
  value       = var.gpu_type == "intel" ? var.jupyterhub_intel_gpu_profile_image : var.jupyterhub_nvidia_gpu_profile_image
  description = "The Docker image used for the JupyterHub GPU profile."
}

output "jupyterhub_extra_resource_limits" {
  value       = var.jupyterhub_extra_resource_limits
  description = "Extra resource limits for JupyterHub, e.g., GPU resources"
}

