output "aws_region" {
  description = "Configured AWS region for this root module."
  value       = var.aws_region
}

output "name_prefix" {
  description = "Naming prefix used for future AWS resources."
  value       = local.name_prefix
}

output "project_tags" {
  description = "Common tags applied through the AWS provider default_tags."
  value       = local.common_tags
}

output "planned_vpc_cidr" {
  description = "Planned VPC CIDR (not yet provisioned)."
  value       = var.vpc_cidr
}

output "planned_kubernetes_version" {
  description = "Planned EKS Kubernetes version (not yet provisioned)."
  value       = var.kubernetes_version
}

output "planned_availability_zones" {
  description = "Planned Availability Zones (not yet provisioned)."
  value       = var.availability_zones
}
