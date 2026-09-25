variable "namespace" {
  description = "Namespace for Argo CD."
  type        = string
  default     = "argocd"
}

variable "chart_version" {
  description = "argo-cd Helm chart version."
  type        = string
  default     = "8.3.0"
}

variable "server_service_type" {
  description = "Service type for argocd-server (ClusterIP for lab; access via port-forward)."
  type        = string
  default     = "ClusterIP"
}
