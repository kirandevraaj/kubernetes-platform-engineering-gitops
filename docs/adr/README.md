# Architecture Decision Records (ADRs)

| ADR | Decision | Status | Evidence |
|---|---|---|---|
| [001](001-terraform-for-aws-infrastructure.md) | Terraform for AWS infrastructure | Accepted | `terraform/`, `5e304cd` |
| [002](002-eks-managed-control-plane.md) | EKS managed control plane | Accepted | EKS lab vs VMware kubeadm |
| [003](003-gitops-with-argo-cd.md) | Git + Argo CD for CD | Accepted | Argo apps, selfHeal |
| [004](004-immutable-image-digest-promotion.md) | Promote by image digest | Accepted | `0.1.4` digest pin |
| [005](005-kustomize-for-environment-overlays.md) | Kustomize overlays | Accepted | `kubernetes/overlays/*` |
| [006](006-prometheus-grafana-observability.md) | Prometheus + Grafana | Accepted | monitoring / observability |
| [007](007-aws-alb-vs-vmware-ingress.md) | MetalLB+ingress vs ALB IP | Accepted | networking docs |
| [008](008-ebs-csi-for-aws-persistent-storage.md) | EBS CSI add-on | Accepted | storage + resilience |
| [009](009-rbac-least-privilege.md) | Least-privilege RBAC | Accepted | security-lab |
| [010](010-python-and-ansible-automation-boundary.md) | Python / Ansible / TF / Argo boundaries | Accepted | automation guide |
| [011](011-disaster-recovery-model.md) | Git+TF+snapshots+runbooks DR | Accepted | DR evidence |
| [012](012-ingress-high-availability.md) | ingress-nginx HA | Accepted | SPOF → HA experiment |
| [013](013-local-path-vs-ebs-storage.md) | local-path vs EBS | Accepted | storage labs |

All decisions **Accepted** for Project 1 scope.
