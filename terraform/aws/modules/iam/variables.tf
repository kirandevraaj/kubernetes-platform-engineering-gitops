variable "name_prefix" {
  description = "Prefix for IAM resource names."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name (used in role naming and trust context)."
  type        = string
}

variable "tags" {
  description = "Additional tags for IAM roles/policies."
  type        = map(string)
  default     = {}
}
