locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "kubernetes-platform-engineering-gitops"
  }

  # Cross-field node count sanity (also enforced later when the node group is added).
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
