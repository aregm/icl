resource "kubernetes_namespace" "x1-hub" {
  metadata {
    name = "x1-hub"
    labels = var.namespace_labels
  }
}

resource "kubernetes_config_map" "config" {
  metadata {
    name = "x1-hub"
    namespace = kubernetes_namespace.x1-hub.id
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
  data = {
    "hub.toml" = <<-EOF
      ingress_domain = "${var.ingress_domain}"
    EOF
  }
}

resource "kubernetes_deployment" "x1-hub" {
  metadata {
    name = "x1-hub"
    namespace = kubernetes_namespace.x1-hub.id
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        "app.kubernetes.io/name" = "x1-hub"
      }
    }
    template {
      metadata {
        labels = {
          "app.kubernetes.io/name" = "x1-hub"
        }
      }
      spec {
        container {
          name = "x1-hub"
          image = "pbchekin/x1-hub:0.0.5"
          command = [
            "python", "-m", "x1.hub.main", "server", "start"
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

resource "kubernetes_service" "x1-hub" {
  metadata {
    name = "x1-hub"
    namespace = kubernetes_namespace.x1-hub.id
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
      "app.kubernetes.io/name" = "x1-hub"
    }
  }
}

resource "kubernetes_ingress_v1" "x1-hub" {
  metadata {
    name = "x1-hub"
    namespace = kubernetes_namespace.x1-hub.id
  }
  spec {
    rule {
      host = "hub.${var.ingress_domain}"
      http {
        path {
          path = "/"
          backend {
            service {
              name = "x1-hub"
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
    namespace = kubernetes_namespace.x1-hub.id
  }
}

resource "kubernetes_cluster_role_binding" "admin" {
  metadata {
    name = "x1-hub-admin"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = "cluster-admin"
  }
  subject {
    kind = "ServiceAccount"
    name = "admin"
    namespace = kubernetes_namespace.x1-hub.id
  }
}
