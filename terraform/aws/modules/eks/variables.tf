variable "name_prefix" {
  description = "Prefix for EKS resource names."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version (for example 1.36)."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the EKS control plane ENIs (private subnets)."
  type        = list(string)
}

variable "node_subnet_ids" {
  description = "Subnet IDs for the managed node group (private subnets)."
  type        = list(string)
}

variable "cluster_role_arn" {
  description = "IAM role ARN for the EKS control plane."
  type        = string
}

variable "node_role_arn" {
  description = "IAM role ARN for the managed node group."
  type        = string
}

variable "cluster_endpoint_private_access" {
  description = "Enable private API server endpoint."
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access" {
  description = "Enable public API server endpoint."
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDR blocks allowed to reach the public EKS API. Must not include 0.0.0.0/0."
  type        = list(string)
}

variable "enable_cluster_logging" {
  description = "Enable EKS control plane CloudWatch logging."
  type        = bool
  default     = false
}

variable "cluster_log_types" {
  description = "Control plane log types when logging is enabled."
  type        = list(string)
  default     = ["api", "audit", "authenticator"]
}

variable "node_instance_type" {
  description = "EC2 instance type for worker nodes."
  type        = string
}

variable "desired_node_count" {
  description = "Desired managed node count."
  type        = number
}

variable "min_node_count" {
  description = "Minimum managed node count."
  type        = number
}

variable "max_node_count" {
  description = "Maximum managed node count."
  type        = number
}

variable "root_volume_size" {
  description = "Root EBS volume size in GiB."
  type        = number
  default     = 20
}

variable "root_volume_type" {
  description = "Root EBS volume type."
  type        = string
  default     = "gp3"
}

variable "vpc_cidr" {
  description = "VPC CIDR used for optional security-group descriptions."
  type        = string
}

variable "tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
