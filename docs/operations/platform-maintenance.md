# Platform maintenance cadence

**Label:** **Recommended operational practice** — not a log of historical Project 1 scheduled maintenance.

Related: [daily-platform-health.md](../checklists/daily-platform-health.md) · [pre-change-checklist.md](../checklists/pre-change-checklist.md)

---

## Daily

| Task | Reference |
|---|---|
| Node/Pod/Application health | [daily-platform-health.md](../checklists/daily-platform-health.md) |
| Argo Synced/Healthy | Same |
| Critical `/health` | VMware VIP; AWS ALB |
| Warning events sample | READ-ONLY `kubectl get events` |

---

## Weekly

| Task | READ-ONLY checks |
|---|---|
| Capacity | Node allocatable vs pod count; AWS **17-pod** density note from DR drill |
| Failed Applications | `kubectl get applications -n argocd` |
| PVC state | Pending/Bound across `storage-lab` |
| Alert review | Prometheus (if rules configured) |
| Backup posture | [dr-baseline-inventory.md](../dr-baseline-inventory.md); AWS Backup assessment (**Observed:** no EKS plan executed) |

---

## Monthly

| Task | Notes |
|---|---|
| RBAC review | [security-rbac.md](../security-rbac.md) |
| Dependency / version review | [platform-version-inventory.md](./platform-version-inventory.md), [toolchain-inventory.md](../toolchain-inventory.md) |
| Documentation drift | Links, observed-vs-untested matrix |
| DR readiness review | [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) — link only |

---

## Quarterly (Design guidance)

| Task | |
|---|---|
| Restore drill (non-prod) | EBS snapshot, namespace delete drills per [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Terraform state backup | [terraform-dr.md](../terraform-dr.md) |

---

## Maintenance types

| Type | Owner | Tooling |
|---|---|---|
| App config | Developer + Git | Argo |
| Cluster add-on | Platform | Helm/GitOps or EKS add-ons |
| AWS infra | Platform | Terraform (when installed) |
| VMware VMs | Platform | Hypervisor — **Not documented in depth here** |

Node cordon/drain: [node-maintenance.md](./node-maintenance.md).
