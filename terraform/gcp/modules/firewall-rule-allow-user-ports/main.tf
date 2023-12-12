resource "google_compute_firewall" "allow-user-ports" {
  name = "allow-user-ports-${var.cluster_name}"
  network = var.network
  allow {
    protocol = "tcp"
    ports = ["32000-34000"]
  }
  source_ranges = [ "0.0.0.0/0" ]
}

