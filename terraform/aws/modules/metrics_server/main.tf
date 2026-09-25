resource "helm_release" "this" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  version    = var.chart_version
  namespace  = var.namespace

  create_namespace = false
  atomic           = true
  wait             = true
  timeout          = 600

  values = [
    yamlencode({
      # Private EKS workers publish InternalIP; prefer that over Hostname.
      # Do not enable kubelet-insecure-tls — kubelet serving cert verification stays on.
      args = [
        "--kubelet-preferred-address-types=InternalIP",
      ]
      metrics = {
        enabled = true
      }
      # Lab footprint: single replica is enough for Metrics API / HPA.
      replicas = 1
    })
  ]
}
