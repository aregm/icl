resource "kubernetes_namespace" "icl-hub" {
  metadata {
    name = "icl-hub"
    labels = var.namespace_labels
  }
}

resource "kubernetes_config_map" "config" {
  metadata {
    name = "icl-hub"
    namespace = kubernetes_namespace.icl-hub.id
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
  data = {
    "hub.toml" = <<-EOF
      ingress_domain = "${var.ingress_domain}"
      use_node_ip_for_user_ports = ${var.use_node_ip_for_user_ports}
      use_external_node_ip_for_user_ports = ${var.use_external_node_ip_for_user_ports}
    EOF
  }
}

resource "kubernetes_deployment" "icl-hub" {
  metadata {
    name = "icl-hub"
    namespace = kubernetes_namespace.icl-hub.id
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        "app.kubernetes.io/name" = "icl-hub"
      }
    }
    template {
      metadata {
        labels = {
          "app.kubernetes.io/name" = "icl-hub"
        }
      }
      spec {
        container {
          name = "icl-hub"
          image = "pbchekin/icl-hub:0.0.4"
          command = [
            "python", "-m", "infractl.hub.main", "server", "start"
          ]
          liveness_probe {
            http_get {
              port = 8000
              path = "/healthz"
            }
          }
          readiness_probe {
            http_get {
              port = 8000
              path = "/healthz"
            }
          }
          volume_mount {
            mount_path = "/app/.x1"
            name = "config"
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.config.metadata.0.name
          }
        }
        service_account_name = "admin"
      }
    }
  }
}

resource "kubernetes_service" "icl-hub" {
  metadata {
    name = "icl-hub"
    namespace = kubernetes_namespace.icl-hub.id
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
  spec {
    type = "ClusterIP"
    port {
      name = "http"
      port = 8000
      target_port = 8000
      protocol = "TCP"
    }
    selector = {
      "app.kubernetes.io/name" = "icl-hub"
    }
  }
}

resource "kubernetes_ingress_v1" "icl-hub" {
  metadata {
    name = "icl-hub"
    namespace = kubernetes_namespace.icl-hub.id
  }
  spec {
    rule {
      host = "hub.${var.ingress_domain}"
      http {
        path {
          path = "/"
          backend {
            service {
              name = "icl-hub"
              port {
                name = "http"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_account" "admin" {
  metadata {
    name = "admin"
    namespace = kubernetes_namespace.icl-hub.id
  }
}

resource "kubernetes_cluster_role_binding" "admin" {
  metadata {
    name = "icl-hub-admin"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = "cluster-admin"
  }
  subject {
    kind = "ServiceAccount"
    name = "admin"
    namespace = kubernetes_namespace.icl-hub.id
  }
}
