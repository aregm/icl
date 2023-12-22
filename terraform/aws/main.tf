module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.0.4"
  attach_cluster_encryption_policy = false
  cluster_enabled_log_types = []
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access = true
  cluster_name = var.cluster_name
  cluster_version = var.cluster_version
  create_cloudwatch_log_group = false
  vpc_id = var.vpc_id
  subnet_ids = var.subnet_ids

  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol = "-1"
      from_port = 0
      to_port = 0
      type = "ingress"
      self = true
    }
    user_ports_incoming_node = {
      description = "Incoming TCP to user ports"
      protocol = "tcp"
      from_port = 32001
      to_port = 33999
      type = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  cluster_security_group_additional_rules = {
    user_ports_incoming_cluster = {
      description = "Incoming TCP to user ports"
      protocol = "tcp"
      from_port = 32001
      to_port = 33999
      type = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  cluster_addons = {
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    coredns = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
      service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn
    }
  }

  eks_managed_node_group_defaults = {
    disk_size = 250
  }

  eks_managed_node_groups = {
    main = {
      min_size = 3
      max_size = 3
      desired_size = 3
      instance_types = ["t3.xlarge"]
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = {
    "ICL/Cluster" = var.cluster_name
    ManagedBy = "Terraform"
  }
}

module "ebs_csi_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.9.2"

  role_name = "${var.cluster_name}-ebs-csi"
  attach_ebs_csi_policy = true

  oidc_providers = {
    ex = {
      provider_arn = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = {
    "ICL/Cluster" = var.cluster_name
    ManagedBy = "Terraform"
  }
}
