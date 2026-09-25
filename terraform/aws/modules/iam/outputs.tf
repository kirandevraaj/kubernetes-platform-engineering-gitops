output "eks_cluster_role_arn" {
  description = "IAM role ARN for the EKS control plane."
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_node_role_arn" {
  description = "IAM role ARN for the EKS managed node group."
  value       = aws_iam_role.eks_node.arn
}

output "aws_load_balancer_controller_role_arn" {
  description = "IAM role ARN for the AWS Load Balancer Controller (Pod Identity)."
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

output "aws_load_balancer_controller_role_name" {
  description = "IAM role name for the AWS Load Balancer Controller."
  value       = aws_iam_role.aws_load_balancer_controller.name
}
