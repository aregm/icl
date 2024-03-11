# https://github.com/intel/xpumanager/tree/master/deployment/kubernetes/monitoring
resource "null_resource" "xpumanager" {
  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -n prometheus -k https://github.com/intel/xpumanager/deployment/kubernetes/daemonset/base?ref=${var.release}
      kubectl apply -n prometheus -f https://raw.githubusercontent.com/intel/xpumanager/${var.release}/deployment/kubernetes/monitoring/service-intel-xpum.yaml
      # TODO: remove namespaceSelector
      # TODO: add label release=prometheus
      kubectl apply -n prometheus -f https://raw.githubusercontent.com/intel/xpumanager/${var.release}/deployment/kubernetes/monitoring/servicemonitor-intel-xpum.yaml
    EOT
  }

  triggers = {
    release = var.release
  }
}

data "http" "xpumanager-dashboard" {
  url = "https://raw.githubusercontent.com/intel/xpumanager/${var.release}/deployment/kubernetes/monitoring/grafana-dashboard.json"
}

resource "local_file" "xpumanager-dashboard" {
  content  = data.http.xpumanager-dashboard.response_body
  filename = "/tmp/xpumanager-dashboard.json"
}

resource "kubernetes_config_map" "xpumanager-dashboard" {
  metadata {
    name = "xpumanager"
    namespace = "prometheus"
    labels = {
      grafana_dashboard = "1"
    }
  }
  data = {
    "xpumanager.json" = data.http.xpumanager-dashboard.response_body
  }
}
