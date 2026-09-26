# Amazon EBS CSI Driver as an EKS managed add-on with EKS Pod Identity.
# The controller ServiceAccount is created by the add-on; Pod Identity binds IAM.

resource "aws_eks_pod_identity_association" "controller" {
  cluster_name    = var.cluster_name
  namespace       = var.namespace
  service_account = var.service_account_name
  role_arn        = var.controller_role_arn
  tags            = var.tags
}

resource "aws_eks_addon" "this" {
  cluster_name                = var.cluster_name
  addon_name                  = "aws-ebs-csi-driver"
  addon_version               = var.addon_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags

  depends_on = [aws_eks_pod_identity_association.controller]
}
