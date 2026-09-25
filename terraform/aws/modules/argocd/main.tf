resource "helm_release" "this" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.chart_version
  namespace        = var.namespace
  create_namespace = true
  atomic           = true
  wait             = true
  timeout          = 900

  values = [
    yamlencode({
      configs = {
        params = {
          "server.insecure" = true
        }
      }
      server = {
        service = {
          type = var.server_service_type
        }
      }
      # Keep the AWS Argo CD install lean for the lab.
      notifications = {
        enabled = false
      }
      dex = {
        enabled = false
      }
      applicationSet = {
        enabled = true
      }
    })
  ]
}
