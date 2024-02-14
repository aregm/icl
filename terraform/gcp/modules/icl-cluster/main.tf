resource "google_container_cluster" "cluster" {
  name = var.cluster_name
  min_master_version = var.node_version
  initial_node_count = 1
  remove_default_node_pool = true
  deletion_protection = false
}

resource "google_container_node_pool" "gpu_pool" {
  name       = "gpu-pool"
  cluster    = google_container_cluster.cluster.name
  node_count = 1

}

resource "google_container_node_pool" "gpu_pool" {
  name       = "gpu-pool"
  cluster    = google_container_cluster.cluster.name
  node_count = 1

  node_config {
    machine_type = var.machine_type
    image_type = "UBUNTU_CONTAINERD"
  }
  deletion_protection = false
  node_version = var.node_version
  min_master_version = var.node_version
  remove_default_node_pool = false
}

output "network" {
  value = google_container_cluster.cluster.network
}

output "cluster_name" {
    value = google_container_cluster.cluster.name
}
