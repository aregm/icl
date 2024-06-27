resource "google_compute_instance" "bastion" {
  name         = var.bastion_name
  machine_type = var.bastion_machine_type
  zone         = var.gcp_zone
 
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }
 
  network_interface {
    network = "default"
    access_config {
      // Include this section to give the instance a public IP address
    }
  }
 
  metadata = {
    ssh-keys = "${var.bastion_username}:${var.bastion_public_key_content}"
  }
 
  tags = var.bastion_tags
}