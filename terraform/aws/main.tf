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
    module.eks,
  ]
}
