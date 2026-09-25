output "helm_release_name" {
  description = "Helm release name for the AWS Load Balancer Controller."
  value       = helm_release.this.name
}

output "namespace" {
  description = "Namespace hosting the controller."
  value       = var.namespace
}

output "service_account_name" {
  description = "ServiceAccount used by the controller."
  value       = var.service_account_name
}
