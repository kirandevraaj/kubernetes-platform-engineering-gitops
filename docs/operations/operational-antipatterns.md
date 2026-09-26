# Operational anti-patterns

Why common shortcuts fail in a GitOps platform lab — and what to do instead.

| Anti-pattern | Risk | Preferred approach |
|---|---|---|
| `kubectl edit` Deployment for durable change | Drift; OutOfSync; untracked rollback | Git change → Argo ([change-ownership.md](./change-ownership.md)) |
| `kubectl apply -f` bypassing Git for prod apps | Source of truth split | Merge to Git |
| Blind `terraform apply` | Unexpected infra diff | `terraform plan`; review; saved plan |
| `terraform destroy` as cleanup | Irrecoverable without DR | Targeted `-destroy` only in disposable labs with backup |
| Manual EBS attach/detach | AZ/volume corruption | Let EBS CSI reconcile ([aws-storage-resilience.md](../aws-storage-resilience.md)) |
| Edit generated ApplicationSet child Apps | Generator will overwrite or fight manual state | Fix template/generator in Git |
| Grant `cluster-admin` to debug | Permanent blast radius | `kubectl auth can-i`; Git RBAC ([security-rbac.md](../security-rbac.md)) |
| Log Secret values in tickets | Credential leak | [incident-evidence.md](./incident-evidence.md) |
| Force pods onto wrong topology | Pending forever; EBS AZ mismatch | Respect nodeAffinity / same-AZ worker |
| Shell-only ops with no docs | Repeat incidents | Runbook + timeline |
| Ignore NotReady (Running ≠ Ready) | Endpoints drop; ingress 503 | [troubleshooting-matrix.md](../troubleshooting/troubleshooting-matrix.md) |
| `kubectl rollout undo` as GitOps rollback | Cluster ≠ Git; re-sync surprises | Git revert → Argo (**Observed** 0.1.5 recovery) |
| Assume backup because ConfigMap exists | Config ≠ data | EBS snapshot / DR index ([dr-lab-evidence.md](../dr-lab-evidence.md)) |
| Assume NetworkPolicy works on AWS lab | **Observed:** not enforced with current CNI | Verify CNI; see [security-rbac.md](../security-rbac.md) |
| Kill Argo controller to "fix" sync | Pauses all reconciliation | Fix repo/manifest; restore controller |

---

## During incidents

**A good operator does not begin by changing the system.**

Begin with impact, failure domain, evidence, desired state — then smallest safe change ([platform-operations-handbook.md](./platform-operations-handbook.md)).
