output "namespace" {
  description = "Argo CD namespace."
  value       = helm_release.this.namespace
}

output "helm_release_name" {
  description = "Argo CD Helm release name."
  value       = helm_release.this.name
}
