output "release_name" {
  description = "Helm release name for Metrics Server."
  value       = helm_release.this.name
}

output "namespace" {
  description = "Namespace where Metrics Server is installed."
  value       = helm_release.this.namespace
}

output "chart_version" {
  description = "Installed Metrics Server Helm chart version."
  value       = helm_release.this.version
}
