resource "google_compute_firewall" "allow-8443-for-ingress" {
  name = "allow-8443-for-ingress-${var.cluster_name}"
  network = var.network
  allow {
    protocol = "tcp"
    ports = ["8443"]
  }
  source_ranges = [ "0.0.0.0/0" ]
}

