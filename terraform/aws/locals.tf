locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  cluster_name = "${local.name_prefix}-eks"

  common_tags = {
    Project     = "kubernetes-platform-engineering-gitops"
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "kubernetes-platform-engineering-gitops"
  }

  node_count_valid = (
    var.min_node_count <= var.desired_node_count &&
    var.desired_node_count <= var.max_node_count
  )
}

check "node_count_ordering" {
  assert {
    condition     = local.node_count_valid
    error_message = "Require min_node_count <= desired_node_count <= max_node_count."
  }
}

check "public_api_not_open_world" {
  assert {
    condition = (
      !var.cluster_endpoint_public_access ||
      (
        length(var.cluster_endpoint_public_access_cidrs) > 0 &&
        !contains(var.cluster_endpoint_public_access_cidrs, "0.0.0.0/0")
      )
    )
    error_message = "When cluster_endpoint_public_access is true, set cluster_endpoint_public_access_cidrs to one or more CIDRs and do not include 0.0.0.0/0."
  }
}
