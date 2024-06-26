resource "google_container_cluster" "cluster" {
  name = var.cluster_name
  # count per zone
  initial_node_count = 1
  node_config {
    machine_type = var.machine_type
    image_type = "UBUNTU_CONTAINERD"
  }
  deletion_protection = false
  node_version = var.node_version
  min_master_version = var.node_version
  remove_default_node_pool = false
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
}

output "network" {
  value = google_container_cluster.cluster.network
}

output "cluster_name" {
    value = google_container_cluster.cluster.name
}
