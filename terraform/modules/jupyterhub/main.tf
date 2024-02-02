locals {
  jupyterhub_default_profile = {
    display_name = "Default"
    description = "Prefect, Modin, Ray"
    kubespawner_override = {
      image = var.jupyterhub_singleuser_default_image
      # required for sudo
      allow_privilege_escalation = true
      # enable cluster admin
      service_account = var.jupyterhub_cluster_admin_enabled ? kubernetes_service_account.admin.0.metadata.0.name : null
      automount_service_account_token = var.jupyterhub_cluster_admin_enabled
    }
    default = true
  }

  jupyterhub_gpu_profile = {
    display_name = "GPU"
    description = "GPU with user mode dependencies"
    kubespawner_override = {
      image = var.jupyterhub_gpu_profile_image
      # required for sudo
      allow_privilege_escalation = true
      # enable cluster admin
      service_account = var.jupyterhub_cluster_admin_enabled ? kubernetes_service_account.admin.0.metadata.0.name : null
      automount_service_account_token = var.jupyterhub_cluster_admin_enabled
      extra_resource_limits = {
        "gpu.intel.com/i915" = "1"
      }
    }
  }

  jupyterhub_gpu_admin_profile = {
    display_name = "GPU with SYS_ADMIN, SYS_PTRACE"
    description = "GPU with SYS_ADMIN, SYS_PTRACE, and user mode dependencies"
    kubespawner_override = {
      image = var.jupyterhub_gpu_profile_image
      # required for sudo
      allow_privilege_escalation = true
      # enable cluster admin
      service_account = var.jupyterhub_cluster_admin_enabled ? kubernetes_service_account.admin.0.metadata.0.name : null
      automount_service_account_token = var.jupyterhub_cluster_admin_enabled
      extra_resource_limits = {
        "gpu.intel.com/i915" = "1"
      }
      extra_container_config = {
        securityContext = {
          allowPrivilegeEscalation = true
          runAsUser = 1000
          capabilities = {
            add = ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"]
          }
        }
      }
    }
  }

  # https://z2jh.jupyter.org/en/latest/resources/reference.html#singleuser-profilelist
  jupyterhub_profiles = concat(
    [
      local.jupyterhub_default_profile,
    ],
    var.jupyterhub_gpu_profile_enabled ? [local.jupyterhub_gpu_profile] : [],
    var.jupyterhub_gpu_profile_enabled ? [local.jupyterhub_gpu_admin_profile] : [],
    var.jupyterhub_profiles,
  )

  jupyterhub_storage = {
    capacity = var.jupyterhub_singleuser_volume_size

    dynamic = {
      storageClass = var.default_storage_class
    }

    extraVolumes = concat(
      !var.shared_volume_enabled ? [] : [
        {
          name = "data"
          persistentVolumeClaim = {
            claimName = module.shared-volume.0.claim_name
          }
        }
      ],
      var.jupyterhub_shared_memory_size == "" ? [] : [
        {
          name = "shared-mem"
          emptyDir = {
            medium = "Memory"
            sizeLimit = "1Gi"
          }
        }
      ],
    )

    extraVolumeMounts = concat(
      !var.shared_volume_enabled ? [] : [
        {
          mountPath = "/data"
          name = "data"
        }
      ],
      var.jupyterhub_shared_memory_size == "" ? [] : [
        {
          mountPath = "/dev/shm"
          name = "shared-mem"
        }
      ]
    )
  }

  # https://z2jh.jupyter.org/en/latest/resources/reference.html#singleuser-extrafiles
  extra_files = {
    settings = {
      mountPath = "/etc/x1/settings.yaml"
      data = merge(
        {
          default_address = var.ingress_domain
        },
        !var.shared_volume_enabled ? {} : {
          (var.ingress_domain) = {
            prefect_shared_volume_mount = "/data"
          }
        },
      )
    }
  }
}

resource "kubernetes_namespace" "jupyterhub" {
  metadata {
    name = "jupyterhub"
    labels = var.namespace_labels
  }
}

resource "helm_release" "jupyterhub" {
  name = "jupyterhub"
  namespace = kubernetes_namespace.jupyterhub.id
  chart = "jupyterhub"
  repository = "https://jupyterhub.github.io/helm-chart"
  version = "3.0.3"
  timeout = 1200
  # See https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/HEAD/jupyterhub/values.yaml
  # See https://zero-to-jupyterhub.readthedocs.io/en/latest/resources/reference.html
  values = [
    yamlencode({
      singleuser = {
        profileList = local.jupyterhub_profiles
      }
    }),
    yamlencode({
      singleuser = {
        storage = local.jupyterhub_storage
      }
    }),
    yamlencode({
      singleuser = {
        extraFiles = local.extra_files
      }
    }),
    <<-EOT
      hub:
        db:
          pvc:
            storage: 1Gi
            storageClassName: "${var.default_storage_class}"
        networkPolicy:
          enabled: false
        extraConfig:
          myConfig.py: |
            c.KubeSpawner.http_timeout = int(180)
      singleuser:
        # https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/customizing/user-environment.html#use-jupyterlab-by-default
        defaultUrl: /lab
        # https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html#kubespawner.KubeSpawner.start_timeout
        startTimeout: 600
        extraEnv:
          JUPYTERHUB_SINGLEUSER_APP: jupyter_server.serverapp.ServerApp
          PREFECT_API_URL: "${var.prefect_api_url}"
          PREFECT_UI_URL: "http://prefect.${var.ingress_domain}"
        networkPolicy:
          enabled: false
      proxy:
        service:
          type: ClusterIP
        chp:
          networkPolicy:
            enabled: false
      prePuller:
        hook:
          enabled: ${var.jupyterhub_pre_puller_enabled}
        continuous:
          enabled: ${var.jupyterhub_pre_puller_enabled}
      cull:
        enabled: true
        timeout: 2592000 # 1 month
      ingress:
        enabled: true
        hosts:
          - jupyter.${var.ingress_domain}
        annotations:
          nginx.ingress.kubernetes.io/proxy-body-size: "0"
    EOT
  ]
}

module "shared-volume" {
  count = var.shared_volume_enabled ? 1 : 0
  source = "../shared-volume-use"
  namespace = kubernetes_namespace.jupyterhub.id
}

resource "kubernetes_service_account" "admin" {
  count = var.jupyterhub_cluster_admin_enabled ? 1 : 0
  metadata {
    name = "admin"
    namespace = kubernetes_namespace.jupyterhub.id
  }
}

resource "kubernetes_cluster_role_binding" "admin" {
  count = var.jupyterhub_cluster_admin_enabled ? 1 : 0
  metadata {
    name = "admin"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = "cluster-admin"
  }
  subject {
    kind = "ServiceAccount"
    name = "admin"
    namespace = kubernetes_namespace.jupyterhub.id
  }
}
