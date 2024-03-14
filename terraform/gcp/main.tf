data "google_client_config" "provider" {}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.my_cluster.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate,
  )
}

provider "google" {
  project = var.gcp_project
  #region  = var.gcp_region
  zone    = var.gcp_zone
}

module "icl-cluster" {
  source = "./modules/icl-cluster"
  cluster_name = var.cluster_name
  node_version = var.node_version
  machine_type = var.machine_type
  gpu_enabled = var.gpu_enabled
  gpu_model = var.gpu_model
  shared_gpu = var.shared_gpu
}

module "firewall-rule-allow-tcp-8443" {
  depends_on = [ module.icl-cluster ]
  source = "./modules/firewall-rule-allow-tcp-8443"
  cluster_name = var.cluster_name
  network = module.icl-cluster.network
}

module "firewall-rule-allow-user-ports" {
  depends_on = [ module.icl-cluster ]
  source = "./modules/firewall-rule-allow-user-ports"
  cluster_name = var.cluster_name
  network = module.icl-cluster.network
}
