resource "google_compute_firewall" "bastion-ssh" {
  name    = "allow-ssh"
  network = "default"
 
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
 
  source_ranges = var.bastion_source_ranges
  target_tags   = ["bastion"]
}
 
resource "google_compute_firewall" "internal" {
  name    = "allow-internal"
  network = "default"
 
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
 
  source_tags = ["bastion"]
  target_tags = ["gke-cluster"]
}