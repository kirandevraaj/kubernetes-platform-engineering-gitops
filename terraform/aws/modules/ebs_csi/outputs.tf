output "addon_name" {
  description = "EKS add-on name."
  value       = aws_eks_addon.this.addon_name
}

output "addon_version" {
  description = "Pinned EBS CSI add-on version."
  value       = aws_eks_addon.this.addon_version
}

output "addon_arn" {
  description = "EKS add-on ARN."
  value       = aws_eks_addon.this.arn
}

output "pod_identity_association_id" {
  description = "Pod Identity association ID for the EBS CSI controller."
  value       = aws_eks_pod_identity_association.controller.association_id
}

output "service_account_name" {
  description = "EBS CSI controller ServiceAccount name."
  value       = var.service_account_name
}

output "namespace" {
  description = "EBS CSI controller ServiceAccount namespace."
  value       = var.namespace
}
