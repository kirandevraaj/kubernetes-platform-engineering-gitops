output "aws_region" {
  description = "Configured AWS region."
  value       = var.aws_region
}

output "name_prefix" {
  description = "Naming prefix for AWS resources."
  value       = local.name_prefix
}

output "project_tags" {
  description = "Common tags applied through the AWS provider default_tags."
  value       = local.common_tags
}

output "vpc_id" {
  description = "Project VPC ID."
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "Project VPC CIDR."
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs."
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs."
  value       = module.vpc.nat_gateway_ids
}

output "eks_cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API endpoint."
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_version" {
  description = "EKS Kubernetes version."
  value       = module.eks.cluster_version
}

output "eks_node_group_name" {
  description = "Managed node group name."
  value       = module.eks.node_group_name
}

output "configure_kubectl" {
  description = "Command to configure kubectl for this cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "argocd_namespace" {
  description = "Argo CD namespace when installed."
  value       = try(module.argocd[0].namespace, null)
}

output "gitops_application_name" {
  description = "Bootstrapped Argo CD Application name."
  value       = try(module.gitops_bootstrap[0].application_name, null)
}
