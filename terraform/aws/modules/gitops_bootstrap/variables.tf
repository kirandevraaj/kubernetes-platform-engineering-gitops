variable "argocd_namespace" {
  description = "Namespace where Argo CD is installed."
  type        = string
  default     = "argocd"
}

variable "git_repo_url" {
  description = "Git repository URL for the AWS overlay."
  type        = string
}

variable "git_target_revision" {
  description = "Git revision (branch/tag/commit) for the Application."
  type        = string
  default     = "main"
}

variable "overlay_path" {
  description = "Path inside the repo for the AWS overlay."
  type        = string
  default     = "kubernetes/overlays/aws"
}

variable "destination_namespace" {
  description = "Namespace where the workload is synced."
  type        = string
  default     = "platform-lab"
}

variable "app_project_name" {
  description = "Argo CD AppProject name for the AWS target."
  type        = string
  default     = "platform-lab-aws"
}

variable "application_name" {
  description = "Argo CD Application name for the AWS target."
  type        = string
  default     = "platform-lab-aws"
}

variable "cluster_name" {
  description = "EKS cluster name (for kubeconfig during bootstrap)."
  type        = string
}

variable "aws_region" {
  description = "AWS region for kubeconfig during bootstrap."
  type        = string
}
