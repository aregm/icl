resource "google_compute_firewall" "bastion-ssh" {
  name    = var.ssh_rule_name
  network = "default"
 
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
 
  source_ranges = var.bastion_source_ranges
  target_tags   = var.bastion_tags
}
 
resource "google_compute_firewall" "internal" {
  name    = var.internal_rule_name
  network = "default"
 
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
 
  source_tags = var.bastion_tags
  target_tags = var.cluster_tags
}