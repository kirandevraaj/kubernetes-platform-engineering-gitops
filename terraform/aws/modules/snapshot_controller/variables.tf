variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "addon_version" {
  description = "Pinned snapshot-controller EKS add-on version."
  type        = string
}

variable "tags" {
  description = "Tags applied to the add-on."
  type        = map(string)
  default     = {}
}
