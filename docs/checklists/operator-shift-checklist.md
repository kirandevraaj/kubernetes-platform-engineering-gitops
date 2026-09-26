# Operator shift checklist

**Beginning of shift** and **end of shift** handoff for Project 1 lab operations.

---

## Start of shift

| # | Task | READ-ONLY command / action | ☐ |
|---|---|---|:---:|
| 1 | Confirm kube contexts | `kubectl config get-contexts` | ☐ |
| 2 | Nodes healthy | `kubectl get nodes` (both envs if applicable) | ☐ |
| 3 | Argo Applications | `kubectl get applications -n argocd` | ☐ |
| 4 | `platform-lab` | Deployment 2/2, digest pin | ☐ |
| 5 | PVC / storage-lab | `kubectl get pvc -n storage-lab` Bound | ☐ |
| 6 | Observability | Prometheus/Grafana pods Ready | ☐ |
| 7 | Alerts / failed Jobs | Prometheus alerts; `kubectl get jobs -A` | ☐ |
| 8 | Recent changes | Git log; Argo revision; Jenkins | ☐ |
| 9 | Capacity | Node pod count; AWS 17-pod density note (**Observed** DR drill) | ☐ |
| 10 | Backup / DR posture | Review [dr-baseline-inventory.md](../dr-baseline-inventory.md) — no secrets | ☐ |

---

## End of shift

| # | Handoff item | ☐ |
|---|---|:---:|
| 1 | Open incidents — severity, owner, next steps | ☐ |
| 2 | Pending changes — PRs, Terraform plans, maintenance | ☐ |
| 3 | Git vs cluster — any OutOfSync Applications | ☐ |
| 4 | Evidence bundles location (if incident) — redacted | ☐ |
| 5 | Runbook / timeline updates needed | ☐ |
| 6 | Escalations outstanding | [escalation.md](../operations/escalation.md) | ☐ |

---

**Design guidance:** Production on-call paging integration — **Not tested in Project 1** ([production-gaps.md](../operations/production-gaps.md)).
