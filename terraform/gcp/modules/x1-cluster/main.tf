resource "google_container_cluster" "x1-cluster" {
  name = var.cluster_name
  # count per zone
  initial_node_count = 1
  node_config {
    machine_type = "e2-standard-4"
  }
  deletion_protection = false
  node_version = var.node_version
  min_master_version = var.node_version
  remove_default_node_pool = false
}

output "network" {
  value = google_container_cluster.x1-cluster.network
}

output "cluster_name" {
    value = google_container_cluster.x1-cluster.name
}
