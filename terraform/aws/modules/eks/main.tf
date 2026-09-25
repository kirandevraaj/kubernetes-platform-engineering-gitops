locals {
  cluster_log_types = var.enable_cluster_logging ? var.cluster_log_types : []
}

data "aws_subnet" "first" {
  id = var.subnet_ids[0]
}

resource "aws_security_group" "cluster_additional" {
  name        = "${var.name_prefix}-eks-cluster-extra"
  description = "Additional EKS control plane security group for ${var.cluster_name}"
  vpc_id      = data.aws_subnet.first.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eks-cluster-extra-sg"
  })
}

resource "aws_security_group" "nodes" {
  name        = "${var.name_prefix}-eks-nodes"
  description = "EKS managed node group security group for ${var.cluster_name}"
  vpc_id      = data.aws_subnet.first.vpc_id

  # Do not set kubernetes.io/cluster/<name>=owned here.
  # That tag must remain only on the EKS primary/cluster SG so the AWS Load
  # Balancer Controller can uniquely identify the cluster security group.
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eks-nodes-sg"
  })
}

resource "aws_security_group_rule" "nodes_intra" {
  type              = "ingress"
  description       = "Node to node"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.nodes.id
  self              = true
}

resource "aws_security_group_rule" "nodes_from_vpc" {
  type              = "ingress"
  description       = "VPC traffic to nodes/pods (ALB target-type ip, kubelet)"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  security_group_id = aws_security_group.nodes.id
}

resource "aws_security_group_rule" "nodes_egress" {
  type              = "egress"
  description       = "Nodes egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.nodes.id
}

resource "aws_security_group_rule" "cluster_additional_egress" {
  type              = "egress"
  description       = "Cluster additional SG egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.cluster_additional.id
}

resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = var.cluster_role_arn
  version  = var.kubernetes_version

  enabled_cluster_log_types = local.cluster_log_types

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.cluster_endpoint_private_access
    endpoint_public_access  = var.cluster_endpoint_public_access
    public_access_cidrs     = var.cluster_endpoint_public_access ? var.cluster_endpoint_public_access_cidrs : null
    security_group_ids      = [aws_security_group.cluster_additional.id]
  }

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  tags = merge(var.tags, {
    Name = var.cluster_name
  })
}

data "aws_eks_addon_version" "vpc_cni" {
  addon_name         = "vpc-cni"
  kubernetes_version = aws_eks_cluster.this.version
  most_recent        = true
}

data "aws_eks_addon_version" "coredns" {
  addon_name         = "coredns"
  kubernetes_version = aws_eks_cluster.this.version
  most_recent        = true
}

data "aws_eks_addon_version" "kube_proxy" {
  addon_name         = "kube-proxy"
  kubernetes_version = aws_eks_cluster.this.version
  most_recent        = true
}

data "aws_eks_addon_version" "pod_identity" {
  addon_name         = "eks-pod-identity-agent"
  kubernetes_version = aws_eks_cluster.this.version
  most_recent        = true
}

resource "aws_eks_addon" "vpc_cni" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "vpc-cni"
  addon_version               = data.aws_eks_addon_version.vpc_cni.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "kube-proxy"
  addon_version               = data.aws_eks_addon_version.kube_proxy.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags
}

resource "aws_eks_addon" "pod_identity" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "eks-pod-identity-agent"
  addon_version               = data.aws_eks_addon_version.pod_identity.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags
}

resource "aws_launch_template" "nodes" {
  name_prefix = "${var.name_prefix}-ng-"

  # Include the cluster primary SG (required) plus the project node SG.
  vpc_security_group_ids = [
    aws_eks_cluster.this.vpc_config[0].cluster_security_group_id,
    aws_security_group.nodes.id,
  ]

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.root_volume_size
      volume_type           = var.root_volume_type
      encrypted             = true
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "disabled"
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = "${var.name_prefix}-node"
    })
  }

  tag_specifications {
    resource_type = "volume"
    tags = merge(var.tags, {
      Name = "${var.name_prefix}-node-root"
    })
  }

  tags = var.tags
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.name_prefix}-managed"
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.node_subnet_ids
  version         = var.kubernetes_version

  scaling_config {
    desired_size = var.desired_node_count
    min_size     = var.min_node_count
    max_size     = var.max_node_count
  }

  update_config {
    max_unavailable = 1
  }

  instance_types = [var.node_instance_type]
  ami_type       = "AL2023_x86_64_STANDARD"
  capacity_type  = "ON_DEMAND"

  launch_template {
    id      = aws_launch_template.nodes.id
    version = aws_launch_template.nodes.latest_version
  }

  labels = {
    "node.kubernetes.io/role" = "worker"
    "workload"                = "platform-lab"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-managed"
  })

  depends_on = [
    aws_eks_addon.vpc_cni,
    aws_eks_addon.kube_proxy,
    aws_eks_addon.pod_identity,
    aws_security_group_rule.nodes_intra,
    aws_security_group_rule.nodes_from_vpc,
    aws_security_group_rule.nodes_egress,
  ]
}

resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "coredns"
  addon_version               = data.aws_eks_addon_version.coredns.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags

  depends_on = [aws_eks_node_group.this]
}
