variable "name_prefix" {
  description = "Prefix used for naming."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "aws_region" {
  description = "AWS region for the controller."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID passed to the controller."
  type        = string
}

variable "controller_role_arn" {
  description = "IAM role ARN for Pod Identity association."
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for the controller."
  type        = string
  default     = "kube-system"
}

variable "service_account_name" {
  description = "Controller ServiceAccount name."
  type        = string
  default     = "aws-load-balancer-controller"
}

variable "chart_version" {
  description = "Helm chart version for aws-load-balancer-controller. Empty uses latest compatible."
  type        = string
  default     = "1.13.4"
}

variable "tags" {
  description = "Tags applied to the Pod Identity association."
  type        = map(string)
  default     = {}
}
