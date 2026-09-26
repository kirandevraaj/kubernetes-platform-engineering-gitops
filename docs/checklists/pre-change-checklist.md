# Pre-change checklist

Use before **any** platform or application change (Git, Terraform, Jenkins, manual lab mutation).

Related: [change-ownership.md](../operations/change-ownership.md) · [post-change-checklist.md](./post-change-checklist.md) · [operational-antipatterns.md](../operations/operational-antipatterns.md)

---

| # | Item | Done | Notes |
|---|---|:---:|---|
| 1 | **Scope documented** — cluster(s), namespace(s), Application name(s) | ☐ | VMware vs AWS explicit |
| 2 | **Blast radius** — users, data, shared components (ingress, Argo, CSI) | ☐ | |
| 3 | **Git state** — branch, PR, known-good commit SHA | ☐ | |
| 4 | **Argo state** — target Applications Synced/Healthy before change | ☐ | |
| 5 | **Current health** — [daily-platform-health.md](./daily-platform-health.md) spot checks | ☐ | |
| 6 | **Rollback plan** — Git revert path; not `kubectl rollout undo` for GitOps apps | ☐ | [git-rollback.md](../runbooks/git-rollback.md) |
| 7 | **Backup / DR** — EBS snapshot or DR runbook if storage/infra touched | ☐ | [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) |
| 8 | **Maintenance window** — stakeholders notified if user-visible | ☐ | **Design guidance** |
| 9 | **Smallest change** — one logical change per merge | ☐ | |
| 10 | **Commands classified** — READ-ONLY vs SAFE MUTATION vs DESTRUCTIVE | ☐ | [runbook-template.md](../runbooks/runbook-template.md) |
| 11 | **Observe plan** — metrics, `/health`, Argo, events during change | ☐ | |
| 12 | **Validate plan** — [post-change-checklist.md](./post-change-checklist.md) ready | ☐ | |

---

## Environment-specific reminders

| Topic | VMware | AWS |
|---|---|---|
| Context | `ckad-lab` | `platform-lab-aws` |
| App image | Do not bump `platform-lab` during Section 26 docs milestone | Same digest pin |
| NetworkPolicy | Calico enforces (**Observed**) | Policy objects may not enforce (**Observed**) — [security-rbac.md](../security-rbac.md) |
| Terraform | N/A for VMware K8s | Local state risk — [terraform-dr.md](../terraform-dr.md) |

**Do not:** `terraform destroy`, delete production PVCs/EBS, mutate global Argo config, or break existing vol `vol-05faa26874d720ecd` without DR plan.
