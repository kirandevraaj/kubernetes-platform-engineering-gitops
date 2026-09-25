resource "aws_eks_pod_identity_association" "this" {
  cluster_name    = var.cluster_name
  namespace       = var.namespace
  service_account = var.service_account_name
  role_arn        = var.controller_role_arn
  tags            = var.tags
}

resource "helm_release" "this" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = var.chart_version
  namespace  = var.namespace

  create_namespace = false
  atomic           = true
  wait             = true
  timeout          = 600

  values = [
    yamlencode({
      clusterName = var.cluster_name
      region      = var.aws_region
      vpcId       = var.vpc_id
      serviceAccount = {
        create = true
        name   = var.service_account_name
        # Pod Identity association is managed outside Helm (no IRSA annotation).
      }
      enableServiceMutatorWebhook = true
      ingressClassParams = {
        create = true
        name   = "alb"
      }
      createIngressClassResource = true
      ingressClass               = "alb"
    })
  ]

  depends_on = [aws_eks_pod_identity_association.this]
}
