variable "cluster_name" {
  description = "EKS cluster name for the EBS CSI add-on and Pod Identity association."
  type        = string
}

variable "controller_role_arn" {
  description = "IAM role ARN assumed by the EBS CSI controller via EKS Pod Identity."
  type        = string
}

variable "addon_version" {
  description = "Pinned aws-ebs-csi-driver EKS add-on version."
  type        = string
}

variable "namespace" {
  description = "Namespace of the EBS CSI controller ServiceAccount."
  type        = string
  default     = "kube-system"
}

variable "service_account_name" {
  description = "ServiceAccount name used by the EBS CSI controller."
  type        = string
  default     = "ebs-csi-controller-sa"
}

variable "tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
