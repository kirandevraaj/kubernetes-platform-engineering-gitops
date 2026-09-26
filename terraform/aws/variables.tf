variable "aws_region" {
  description = "AWS region for the platform-lab AWS environment."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Short project name used in resource naming."
  type        = string
  default     = "platform-lab"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name)) && length(var.project_name) >= 3 && length(var.project_name) <= 32
    error_message = "project_name must be 3-32 characters of lowercase letters, digits, and hyphens."
  }
}

variable "environment" {
  description = "Environment name used in naming and the Environment tag (aws-lab)."
  type        = string
  default     = "aws-lab"

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
  description = "EKS Kubernetes version (standard support)."
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

variable "root_volume_size" {
  description = "Root EBS volume size (GiB) for worker nodes."
  type        = number
  default     = 20

  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 100
    error_message = "root_volume_size must be between 20 and 100 GiB."
  }
}

variable "enable_single_nat_gateway" {
  description = "Use one NAT Gateway for private subnets (cost-conscious lab default). Set false for one NAT per AZ."
  type        = bool
  default     = true
}

variable "cluster_endpoint_private_access" {
  description = "Enable the private EKS API endpoint."
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access" {
  description = "Enable the public EKS API endpoint (must be paired with restricted CIDRs)."
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public EKS API. Required when public access is enabled. Must not include 0.0.0.0/0."
  type        = list(string)

  validation {
    condition     = length(var.cluster_endpoint_public_access_cidrs) > 0
    error_message = "cluster_endpoint_public_access_cidrs must list at least one CIDR (your public IP/32)."
  }

  validation {
    condition     = !contains(var.cluster_endpoint_public_access_cidrs, "0.0.0.0/0")
    error_message = "cluster_endpoint_public_access_cidrs must not include 0.0.0.0/0."
  }
}

variable "enable_cluster_logging" {
  description = "Enable EKS control plane logs to CloudWatch (cost driver; off by default for the lab)."
  type        = bool
  default     = false
}

variable "git_repo_url" {
  description = "Git repository URL used by Argo CD for the AWS overlay."
  type        = string
  default     = "https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git"
}

variable "git_target_revision" {
  description = "Git revision for the AWS Argo CD Application."
  type        = string
  default     = "main"
}

variable "install_aws_load_balancer_controller" {
  description = "Install AWS Load Balancer Controller via Helm."
  type        = bool
  default     = true
}

variable "install_metrics_server" {
  description = "Install Metrics Server via Helm (required for HPA CPU/memory metrics on EKS)."
  type        = bool
  default     = true
}

variable "install_argocd" {
  description = "Install Argo CD via Helm into the EKS cluster."
  type        = bool
  default     = true
}

variable "bootstrap_gitops" {
  description = "Create the AWS AppProject/Application so Argo CD owns kubernetes/overlays/aws."
  type        = bool
  default     = true
}

variable "install_ebs_csi_driver" {
  description = "Install the Amazon EBS CSI Driver as an EKS managed add-on with Pod Identity."
  type        = bool
  default     = true
}

variable "ebs_csi_addon_version" {
  description = "Pinned aws-ebs-csi-driver EKS add-on version (from describe-addon-versions for the cluster Kubernetes version)."
  type        = string
  default     = "v1.66.0-eksbuild.1"
}

variable "install_snapshot_controller" {
  description = "Install the EKS managed CSI snapshot-controller add-on (VolumeSnapshot CRDs + controller)."
  type        = bool
  default     = true
}

variable "snapshot_controller_addon_version" {
  description = "Pinned snapshot-controller EKS add-on version (from describe-addon-versions for the cluster Kubernetes version)."
  type        = string
  default     = "v8.6.0-eksbuild.8"
}

variable "enable_storage_resilience_test_nodegroup" {
  description = "Create a temporary single-AZ EKS managed node group for the EBS storage-resilience experiment. Default false; enable only for the lab, then destroy."
  type        = bool
  default     = false
}

variable "storage_resilience_test_az" {
  description = "AZ for the temporary storage-resilience node group (must match the EBS volume AZ under test)."
  type        = string
  default     = "ap-south-1b"
}
