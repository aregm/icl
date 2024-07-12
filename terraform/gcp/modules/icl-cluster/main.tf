resource "google_container_cluster" "cluster" {
  name = var.cluster_name
  min_master_version = var.node_version
  initial_node_count = 1
  remove_default_node_pool = true
  deletion_protection = false
}

resource "google_container_node_pool" "pool" {
  count = var.gpu_enabled ? 0 : 1
  name = "pool"
  cluster = google_container_cluster.cluster.name
  node_count = 1

  node_config {
    tags = ["gke-cluster"]
    image_type   = "cos_containerd"
    machine_type = var.machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/trace.append",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
    ]
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

resource "google_container_node_pool" "exclusive_gpu_pool" {
  count = var.gpu_enabled && !var.shared_gpu ? 1 : 0
  name       = "excusive-gpu-pool"
  cluster    = google_container_cluster.cluster.name
  node_count = var.node_count

  node_config {
    tags = ["gke-cluster"]
    image_type   = "cos_containerd"
    machine_type = var.machine_type

    guest_accelerator {
      type  = var.gpu_model
      count = var.gpu_count
      gpu_driver_installation_config {
        gpu_driver_version = var.gke_gpu_driver_version
      }
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/trace.append",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

resource "google_container_node_pool" "shared_gpu_pool" {
  count = var.gpu_enabled && var.shared_gpu ? 1 : 0
  name       = "shared-gpu-pool"
  cluster    = google_container_cluster.cluster.name
  node_count = var.node_count

  node_config {
    tags = ["gke-cluster"]
    image_type   = "cos_containerd"
    machine_type = var.machine_type

    guest_accelerator {
      type  = var.gpu_model
      count = var.gpu_count
      gpu_driver_installation_config {
        gpu_driver_version = var.gke_gpu_driver_version
      }
      gpu_sharing_config {
        gpu_sharing_strategy = "TIME_SHARING"
        max_shared_clients_per_gpu = 30
      }
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/trace.append",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

output "network" {
  value = google_container_cluster.cluster.network
}

output "cluster_name" {
    value = google_container_cluster.cluster.name
}