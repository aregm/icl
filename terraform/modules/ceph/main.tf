resource "helm_release" "ceph_operator" {
  name = "rook-ceph"
  namespace = "rook-ceph"
  create_namespace = true
  repository = "https://charts.rook.io/release"
  chart = "rook-ceph"
  version = var.release
  # https://rook.io/docs/rook/v1.11/Helm-Charts/operator-chart/#configuration
  # https://github.com/rook/rook/blob/release-1.12/deploy/charts/rook-ceph/values.yaml
  values = [
    yamlencode({
      allowLoopDevices = var.ceph_allow_loop_devices
    }),
  ]
}

resource "helm_release" "ceph_cluster" {
  depends_on = [helm_release.ceph_operator]
  name = "rook-ceph-cluster"
  namespace = "rook-ceph"
  create_namespace = true
  repository = "https://charts.rook.io/release"
  chart = "rook-ceph-cluster"
  version = var.release
  # https://github.com/rook/rook/blob/release-1.9/Documentation/Helm-Charts/ceph-cluster-chart.md
  # https://github.com/rook/rook/blob/release-1.9/deploy/charts/rook-ceph-cluster/values.yaml
  values = length(var.ceph_devices) > 0 ? [
    <<-EOT
      toolbox:
        enabled: true
      cephClusterSpec:
        dashboard:
          enabled: true
          ssl: false
        storage:
          useAllNodes: true
          useAllDevices: false
          devices: ${jsonencode(var.ceph_devices)}
    EOT
  ] : [
    <<-EOT
      toolbox:
        enabled: true
      cephClusterSpec:
        dashboard:
          enabled: true
          ssl: false
        storage:
          deviceFilter: "${var.ceph_device_filter}"
        monitoring:
          enabled: true
          createPrometheusRules: true 
        # cephObjectStores:
        # TODO: instances == number of nodes
        # TODO: increase CPU and RAM limits for the gateway
    EOT
  ]
}

# TODO: create Ceph users
# https://github.com/rook/rook/blob/release-1.9/deploy/examples/object-user.yaml

resource "kubernetes_ingress_v1" "dashboard" {
  depends_on = [helm_release.ceph_cluster]
  metadata {
    name = "dashboard"
    namespace = "rook-ceph"
  }
  spec {
    rule {
      host = "ceph.${var.ingress_domain}"
      http {
        path {
          path = "/"
          backend {
            service {
              name = "rook-ceph-mgr-dashboard"
              port {
                name = "http-dashboard"
              }
            }
          }
        }
      }
    }
  }
}

