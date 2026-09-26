output "addon_name" {
  description = "EKS add-on name."
  value       = aws_eks_addon.snapshot_controller.addon_name
}

output "addon_version" {
  description = "Installed snapshot-controller add-on version."
  value       = aws_eks_addon.snapshot_controller.addon_version
}

output "addon_arn" {
  description = "Add-on ARN."
  value       = aws_eks_addon.snapshot_controller.arn
}
