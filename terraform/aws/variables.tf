variable "aws_region" {
  description = "AWS region for the platform-lab AWS environment."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Short project name used in resource naming and tags."
  type        = string
  default     = "platform-lab"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name)) && length(var.project_name) >= 3 && length(var.project_name) <= 32
    error_message = "project_name must be 3-32 characters of lowercase letters, digits, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (for example aws)."
  type        = string
  default     = "aws"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, digits, and hyphens."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the project VPC."
  type        = string
  default     = "10.50.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR."
  }
}

variable "availability_zones" {
  description = "Exactly two Availability Zones used by the VPC and EKS."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "availability_zones must contain exactly two zones."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)."
  type        = list(string)
  default     = ["10.50.0.0/20", "10.50.16.0/20"]

  validation {
    condition     = length(var.public_subnet_cidrs) == 2 && alltrue([for c in var.public_subnet_cidrs : can(cidrnetmask(c))])
    error_message = "public_subnet_cidrs must be two valid IPv4 CIDRs."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ) for EKS worker nodes."
  type        = list(string)
  default     = ["10.50.32.0/20", "10.50.48.0/20"]

  validation {
    condition     = length(var.private_subnet_cidrs) == 2 && alltrue([for c in var.private_subnet_cidrs : can(cidrnetmask(c))])
    error_message = "private_subnet_cidrs must be two valid IPv4 CIDRs."
  }
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.36"

  validation {
    condition     = can(regex("^1\\.(3[4-9]|[4-9][0-9])$", var.kubernetes_version))
    error_message = "kubernetes_version must look like 1.XX (for example 1.36)."
  }
}

variable "node_instance_type" {
  description = "EC2 instance type for the EKS managed node group."
  type        = string
  default     = "t3.medium"
}

variable "desired_node_count" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2

  validation {
    condition     = var.desired_node_count >= 1 && var.desired_node_count <= 10
    error_message = "desired_node_count must be between 1 and 10."
  }
}

variable "min_node_count" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 1

  validation {
    condition     = var.min_node_count >= 1 && var.min_node_count <= 10
    error_message = "min_node_count must be between 1 and 10."
  }
}

variable "max_node_count" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 3

  validation {
    condition     = var.max_node_count >= 1 && var.max_node_count <= 10
    error_message = "max_node_count must be between 1 and 10."
  }
}

variable "enable_single_nat_gateway" {
  description = "Use one NAT Gateway for private subnets (cost-conscious lab default)."
  type        = bool
  default     = true
}
