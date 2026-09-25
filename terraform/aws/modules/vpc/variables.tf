variable "name_prefix" {
  description = "Prefix for VPC resource names."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "availability_zones" {
  description = "Availability Zones for subnets (exactly two for this lab)."
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs (one per AZ)."
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs (one per AZ)."
  type        = list(string)
}

variable "enable_single_nat_gateway" {
  description = "If true, create one NAT Gateway in the first public subnet and share it. If false, create one NAT per AZ."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags merged onto resources (provider default_tags still apply)."
  type        = map(string)
  default     = {}
}
