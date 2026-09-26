# EKS managed CSI snapshot controller add-on (VolumeSnapshot CRDs + controller).
# Pinned for Kubernetes 1.36 compatibility. Does not replace EBS CSI driver.

resource "aws_eks_addon" "snapshot_controller" {
  cluster_name                = var.cluster_name
  addon_name                  = "snapshot-controller"
  addon_version               = var.addon_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags
}
