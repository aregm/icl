resource "kubernetes_namespace" "prefect" {
  metadata {
    name = "prefect"
    labels = var.namespace_labels
  }
}

locals {
  worker_namespace_manifest = templatefile(
    "${path.module}/agent-namespace.yaml",
    {
      namespace_labels = var.namespace_labels
    }
  )
}

# Use "null_resource" with "kubectl apply" instead of "kubernetes_namespace" because the default
# namespace for Prefect worker is "default" and resource "kubernetes_namespace" fails when namespace
# already exists. At the same time we have to apply "namespace_labels" to the namespace.
resource "null_resource" "worker-namespace" {
  provisioner "local-exec" {
    command = <<-EOT
      cat <<'EOF' | kubectl apply -f -
      ${local.worker_namespace_manifest}
      EOF
    EOT
  }

  triggers = {
    checksum = sha256(local.worker_namespace_manifest)
  }
}

resource "helm_release" "prefect-server" {
  name = "prefect-server"
  namespace = kubernetes_namespace.prefect.id
  repository = "https://prefecthq.github.io/prefect-helm"
  chart = "prefect-server"
  version = var.chart_version
  timeout = 900
  values = [
    <<-EOT
      namespaceOverride: prefect
      global:
        prefect:
          image:
            prefectTag: "${var.server_image_tag}"
      server:
        prefectApiUrl: "${var.api_url == "" ? "http://prefect.${var.ingress_domain}/api" : var.api_url}"
      service:
        type: ClusterIP
      ingress:
        enabled: true
        host:
          hostname: prefect.${var.ingress_domain}
      # TODO: install postgresql separately, bundled postgresql subchart is not recommended for production
      postgresql:
        enabled: true
        auth:
          password: e0e2eda98519739fa4656e4cc502841b
    EOT
  ]
}

resource "helm_release" "prefect-worker" {
  depends_on = [null_resource.worker-namespace, helm_release.prefect-server]
  name = "prefect-worker"
  namespace = var.worker_namespace
  repository = "https://prefecthq.github.io/prefect-helm"
  chart = "prefect-worker"
  version = var.chart_version
  timeout = 600
  values = [
    <<-EOT
      namespaceOverride: ${var.worker_namespace}
      worker:
        image:
          prefectTag: "${var.worker_image_tag}"
        apiConfig: selfHostedServer
        selfHostedServerApiConfig:
          apiUrl: http://prefect-server.prefect:4200/api
        config:
          workPool: "${var.work_pool_name}"
          type: kubernetes
          workQueues:
            - prod
        resources: {}
    EOT
  ]
}

module "shared-volume" {
  count = var.shared_volume_enabled ? 1 : 0
  depends_on = [null_resource.worker-namespace]
  source = "../shared-volume-use"
  namespace = "default"
}
