# Observed vs untested matrix

Prevents overstating Project 1 coverage. **Evidence** links are authoritative lab write-ups.

| Scenario | Observed? | Evidence | Measured? | Runbook | Notes |
|---|---|---|---|---|---|
| Pod delete recovery | Yes | Pod failure lab | ~10–14 s | [pod-failure.md](../runbooks/pod-failure.md) | ≠ node failure |
| Readiness failure | Yes | Readiness experiment | Qualitative | [pod-not-ready.md](../runbooks/pod-not-ready.md) | Running ≠ Ready |
| Argo live drift selfHeal | Yes | [dr-lab-evidence.md](../dr-lab-evidence.md) | ~6 s | [argo-outofsync.md](../runbooks/argo-outofsync.md) | VMware |
| Rollout failure 0.1.5 | Yes | Git rollback lab | Qualitative | [failed-rollout.md](../runbooks/failed-rollout.md) | Git → Argo |
| VMware worker failure | Yes | Worker/kubelet lab | Qualitative | [worker-node-failure.md](../runbooks/worker-node-failure.md) | |
| AWS worker + EBS recovery | Yes | [aws-storage-resilience.md](../aws-storage-resilience.md) | ~6.3 min | Same | No drain used |
| Ingress VMware SPOF → HA | Yes | Networking labs | Qualitative | [ingress-unavailable.md](../runbooks/ingress-unavailable.md) | 2 replicas |
| VMware local-path storage | Yes | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) | Pod delete | [pvc-pv-troubleshooting.md](../runbooks/pvc-pv-troubleshooting.md) | |
| EBS snapshot restore | Yes | [dr-lab-evidence.md](../dr-lab-evidence.md) | 72s / 15s | [ebs-snapshot-restore.md](../runbooks/ebs-snapshot-restore.md) | Cross-NS lesson |
| Namespace delete recovery | Yes | dr-lab-evidence | ~23 s | [git-argo-recovery.md](../runbooks/git-argo-recovery.md) | |
| Argo Application delete | Yes | dr-lab-evidence | ~6–14 s | git-argo-recovery | Workloads may remain |
| Git bad commit revert | Yes | dr-lab-evidence | ~5–10 s sync | [git-rollback.md](../runbooks/git-rollback.md) | |
| RBAC / SA / PSA | Yes | [security-rbac.md](../security-rbac.md) | can-i tests | [rbac-access-denied.md](../runbooks/rbac-access-denied.md) | |
| NetworkPolicy enforce | Partial | security-rbac | VMware yes / AWS no | [networkpolicy-troubleshooting.md](../runbooks/networkpolicy-troubleshooting.md) | **Observed** split |
| HPA scale | Yes | HPA labs | Env-specific | [hpa-not-scaling.md](../runbooks/hpa-not-scaling.md) | 2→4 / 2→3 |
| Prometheus scrape | Yes | Observability labs | Qualitative | [prometheus-target-down.md](../runbooks/prometheus-target-down.md) | `/metrics` |
| Grafana OOM fix | Yes | GitOps resource bump | Qualitative | [grafana-unavailable.md](../runbooks/grafana-unavailable.md) | |
| Argo ComparisonError | Yes | waves-health kustomize | Qualitative | argo-outofsync | Path fix |
| AWS Backup EKS restore | No | dr-lab-evidence assessment | N/A | [aws-backup-eks-dr.md](../aws-backup-eks-dr.md) | Not executed |
| Full EKS rebuild | No | disaster-scenario-matrix | N/A | [aws-eks-disaster-recovery.md](../runbooks/aws-eks-disaster-recovery.md) | Plan-only |
| Region failure | No | — | N/A | — | Design only |
| kubectl drain maintenance | No | aws-storage-resilience | N/A | [node-maintenance.md](./node-maintenance.md) | Design guidance |
| Argo controller kill/recover | No | — | N/A | [argocd-controller-unavailable.md](../runbooks/argocd-controller-unavailable.md) | Documented only |
| GitHub/registry outage | No | — | N/A | github/registry runbooks | Design guidance |

---

## Related

- [operational-readiness-assessment.md](./operational-readiness-assessment.md)
- [production-gaps.md](./production-gaps.md)
