resource "helm_release" "kubernetes-dashboard" {
  name = "kubernetes-dashboard"
  namespace = "kubernetes-dashboard"
  create_namespace = true
  repository = "https://kubernetes.github.io/dashboard/"
  chart = "kubernetes-dashboard"
  version = var.release
  timeout = 600
  values = [
    <<-EOT
      app:
        ingress:
          enabled: true
          hosts:
            - dashboard.${var.ingress_domain}
          useDefaultIngressClass: true
          useDefaultAnnotations: true
          issuer:
            scope: disabled
          tls:
            enabled: false
      kong:
        proxy:
          type: ClusterIP
          http:
            enabled: true
      cert-manager:
        enabled: false
      nginx:
        enabled: false
    EOT
  ]
}

resource "kubernetes_service_account" "admin-user" {
  depends_on = [helm_release.kubernetes-dashboard]
  metadata {
    name = "admin-user"
    namespace = "kubernetes-dashboard"
  }
}

resource "kubernetes_cluster_role_binding" "kubernetes-dashboard-admin" {
  depends_on = [helm_release.kubernetes-dashboard]
  metadata {
    name = "kubernetes-dashboard-admin"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = "cluster-admin"
  }
  subject {
    kind = "ServiceAccount"
    name = "admin-user"
    namespace = "kubernetes-dashboard"
  }
}
