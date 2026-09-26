module "vpc" {
  source = "./modules/vpc"

  name_prefix               = local.name_prefix
  vpc_cidr                  = var.vpc_cidr
  availability_zones        = var.availability_zones
  public_subnet_cidrs       = var.public_subnet_cidrs
  private_subnet_cidrs      = var.private_subnet_cidrs
  enable_single_nat_gateway = var.enable_single_nat_gateway
  tags                      = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  name_prefix  = local.name_prefix
  cluster_name = local.cluster_name
  tags         = local.common_tags
}

module "eks" {
  source = "./modules/eks"

  name_prefix                          = local.name_prefix
  cluster_name                         = local.cluster_name
  kubernetes_version                   = var.kubernetes_version
  subnet_ids                           = module.vpc.private_subnet_ids
  node_subnet_ids                      = module.vpc.private_subnet_ids
  cluster_role_arn                     = module.iam.eks_cluster_role_arn
  node_role_arn                        = module.iam.eks_node_role_arn
  cluster_endpoint_private_access      = var.cluster_endpoint_private_access
  cluster_endpoint_public_access       = var.cluster_endpoint_public_access
  cluster_endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs
  enable_cluster_logging               = var.enable_cluster_logging
  node_instance_type                   = var.node_instance_type
  desired_node_count                   = var.desired_node_count
  min_node_count                       = var.min_node_count
  max_node_count                       = var.max_node_count
  root_volume_size                     = var.root_volume_size
  vpc_cidr                             = var.vpc_cidr
  tags                                 = local.common_tags

  depends_on = [module.iam]
}

module "aws_load_balancer_controller" {
  count  = var.install_aws_load_balancer_controller ? 1 : 0
  source = "./modules/aws_load_balancer_controller"

  name_prefix         = local.name_prefix
  cluster_name        = module.eks.cluster_name
  aws_region          = var.aws_region
  vpc_id              = module.vpc.vpc_id
  controller_role_arn = module.iam.aws_load_balancer_controller_role_arn
  tags                = local.common_tags

  depends_on = [
    module.eks,
  ]
}

module "metrics_server" {
  count  = var.install_metrics_server ? 1 : 0
  source = "./modules/metrics_server"

  depends_on = [
    module.eks,
  ]
}

module "argocd" {
  count  = var.install_argocd ? 1 : 0
  source = "./modules/argocd"

  depends_on = [
    module.eks,
    module.aws_load_balancer_controller,
    module.metrics_server,
  ]
}

module "gitops_bootstrap" {
  count  = var.bootstrap_gitops && var.install_argocd ? 1 : 0
  source = "./modules/gitops_bootstrap"

  git_repo_url          = var.git_repo_url
  git_target_revision   = var.git_target_revision
  overlay_path          = "kubernetes/overlays/aws"
  destination_namespace = "platform-lab"
  cluster_name          = module.eks.cluster_name
  aws_region            = var.aws_region

  depends_on = [module.argocd]
}

module "ebs_csi" {
  count  = var.install_ebs_csi_driver ? 1 : 0
  source = "./modules/ebs_csi"

  cluster_name        = module.eks.cluster_name
  controller_role_arn = module.iam.ebs_csi_controller_role_arn
  addon_version       = var.ebs_csi_addon_version
  tags                = local.common_tags

  # Attribute references establish ordering without forcing a full EKS module
  # refresh/plan (avoids unrelated SG/addon drift being applied with storage work).
}

module "snapshot_controller" {
  count  = var.install_snapshot_controller ? 1 : 0
  source = "./modules/snapshot_controller"

  cluster_name  = module.eks.cluster_name
  addon_version = var.snapshot_controller_addon_version
  tags          = local.common_tags

  # CSI VolumeSnapshot CRDs/controller. Independent of EBS CSI Pod Identity.
  depends_on = [module.eks]
}

# Temporary same-AZ worker for EBS node-failure resilience lab ONLY.
# Subnet is restricted to the EBS volume AZ. Destroy after the experiment.
locals {
  private_subnet_by_az = {
    for idx, az in var.availability_zones :
    az => module.vpc.private_subnet_ids[idx]
  }
}

resource "aws_eks_node_group" "storage_resilience_test" {
  count = var.enable_storage_resilience_test_nodegroup ? 1 : 0

  cluster_name    = module.eks.cluster_name
  node_group_name = "storage-resilience-test-1b"
  node_role_arn   = module.iam.eks_node_role_arn
  subnet_ids      = [local.private_subnet_by_az[var.storage_resilience_test_az]]
  version         = var.kubernetes_version

  scaling_config {
    desired_size = 1
    min_size     = 0
    max_size     = 1
  }

  update_config {
    max_unavailable = 1
  }

  instance_types = [var.node_instance_type]
  ami_type       = "AL2023_x86_64_STANDARD"
  capacity_type  = "ON_DEMAND"

  launch_template {
    id      = module.eks.node_launch_template_id
    version = module.eks.node_launch_template_latest_version
  }

  labels = {
    "node.kubernetes.io/role"            = "worker"
    "workload"                           = "storage-resilience-test"
    "platform-lab.io/storage-resilience" = "temporary"
  }

  tags = merge(local.common_tags, {
    Name    = "storage-resilience-test-1b"
    Purpose = "temporary-ebs-storage-resilience-lab"
  })

  lifecycle {
    create_before_destroy = false
  }
}

# Destroy-safety: this resource is destroyed first (it depends on K8s components).
# Its destroy-time provisioner deletes Argo Applications / Ingress while the
# cluster and AWS Load Balancer Controller are still available, so ALB finalizers
# can complete before EKS/VPC teardown.
resource "null_resource" "destroy_safety" {
  triggers = {
    cluster_name = module.eks.cluster_name
    aws_region   = var.aws_region
  }

  provisioner "local-exec" {
    when    = destroy
    command = "bash ${path.module}/scripts/pre-destroy-cleanup.sh"
    environment = {
      CLUSTER_NAME     = self.triggers.cluster_name
      AWS_REGION       = self.triggers.aws_region
      ARGOCD_NAMESPACE = "argocd"
      APP_NAMESPACE    = "platform-lab"
    }
  }

  depends_on = [
    module.gitops_bootstrap,
    module.argocd,
    module.aws_load_balancer_controller,
    module.metrics_server,
    module.ebs_csi,
    module.snapshot_controller,
    module.eks,
  ]
}
