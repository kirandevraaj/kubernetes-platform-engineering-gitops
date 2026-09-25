# Temporary bootstrap only: kubectl-applies AppProject + Application after Argo CD
# Helm install. Argo CD then owns kubernetes/overlays/aws. Terraform does not manage
# Deployment/Service/Ingress for the application.
#
# Why not kubernetes_manifest? Argo CRDs do not exist until the Helm release completes,
# so OpenAPI-based kubernetes_manifest planning fails on a fresh cluster.

locals {
  app_project_manifest = templatefile("${path.module}/templates/appproject.yaml.tftpl", {
    name                  = var.app_project_name
    namespace             = var.argocd_namespace
    git_repo_url          = var.git_repo_url
    destination_namespace = var.destination_namespace
  })

  application_manifest = templatefile("${path.module}/templates/application.yaml.tftpl", {
    name                  = var.application_name
    namespace             = var.argocd_namespace
    project               = var.app_project_name
    git_repo_url          = var.git_repo_url
    git_target_revision   = var.git_target_revision
    overlay_path          = var.overlay_path
    destination_namespace = var.destination_namespace
  })
}

resource "null_resource" "bootstrap" {
  triggers = {
    application_name = var.application_name
    app_project_name = var.app_project_name
    cluster_name     = var.cluster_name
    aws_region       = var.aws_region
    app_project      = sha256(local.app_project_manifest)
    application      = sha256(local.application_manifest)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    # replace() strips Windows CRLF so bash does not see "pipefail\r".
    command = replace(<<-EOT
      set -euo pipefail
      aws eks update-kubeconfig --name "${var.cluster_name}" --region "${var.aws_region}" >/dev/null
      kubectl wait --for=condition=Established crd/applications.argoproj.io --timeout=300s
      kubectl wait --for=condition=Established crd/appprojects.argoproj.io --timeout=300s
      cat <<'EOF' | kubectl apply -f -
${local.app_project_manifest}
EOF
      cat <<'EOF' | kubectl apply -f -
${local.application_manifest}
EOF
    EOT
    , "\r", "")
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["/bin/bash", "-c"]
    command = replace(<<-EOT
      set -euo pipefail
      aws eks update-kubeconfig --name "${self.triggers.cluster_name}" --region "${self.triggers.aws_region}" >/dev/null || exit 0
      kubectl -n argocd delete application "${self.triggers.application_name}" --wait=true --timeout=10m || true
      kubectl -n argocd delete appproject "${self.triggers.app_project_name}" --wait=true --timeout=5m || true
    EOT
    , "\r", "")
  }
}
