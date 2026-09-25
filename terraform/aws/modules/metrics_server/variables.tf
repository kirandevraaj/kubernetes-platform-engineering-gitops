variable "namespace" {
  description = "Namespace for Metrics Server (kube-system on EKS)."
  type        = string
  default     = "kube-system"
}

variable "chart_version" {
  description = "metrics-server Helm chart version (Artifact Hub / kubernetes-sigs)."
  type        = string
  default     = "3.14.0"
}
