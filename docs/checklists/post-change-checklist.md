# Post-change verification checklist

Run after merge, sync, Terraform apply (when approved), or controlled lab mutation.

---

| # | Area | Verification | Command / check (READ-ONLY) | Pass |
|---|---|---|---|:---:|
| 1 | **Git** | Expected commit on main | `git log -1 --oneline` | ☐ |
| 2 | **Jenkins** | Build green if CI required | Jenkins UI | ☐ |
| 3 | **Argo** | Application Synced/Healthy | `kubectl get application -n argocd` | ☐ |
| 4 | **Deployment** | Available = desired | `kubectl get deploy -n platform-lab` | ☐ |
| 5 | **Pods** | Running + Ready | `kubectl get pods -n platform-lab` | ☐ |
| 6 | **Service** | ClusterIP present | `kubectl get svc -n platform-lab` | ☐ |
| 7 | **Endpoints** | Addresses match ready pods | `kubectl get endpointslices -n platform-lab` | ☐ |
| 8 | **Ingress (VMware)** | HTTP 200 | `curl -H "Host: platform-lab.local" http://192.168.56.200/health` | ☐ |
| 9 | **ALB (AWS)** | Target healthy, `/health` 200 | ALB check (console/CLI) | ☐ |
| 10 | **Metrics** | Prometheus target UP for app | Prometheus UI | ☐ |
| 11 | **HPA** | Replicas within min/max | `kubectl get hpa -n platform-lab` | ☐ |
| 12 | **Storage** | PVC Bound if touched | `kubectl get pvc -n storage-lab` | ☐ |
| 13 | **Application version** | `0.1.4` + digest unchanged unless change intended | image field on Deployment | ☐ |
| 14 | **Events** | No new Warning storm | `kubectl get events -n platform-lab --sort-by='.lastTimestamp'` | ☐ |
| 15 | **Documentation** | Runbook/checklist updated if new behavior observed | N/A | ☐ |

---

## Rollback trigger

If any critical row fails and cannot be fixed forward within agreed window:

1. Git revert to known-good SHA (**SAFE MUTATION** in Git).
2. Wait for Argo reconcile (**Observed:** sync often seconds — [dr-lab-evidence.md](../dr-lab-evidence.md)).
3. Re-run this checklist.

DR detail: [dr-lab-evidence.md](../dr-lab-evidence.md) — do not duplicate Section 25 procedures here.
