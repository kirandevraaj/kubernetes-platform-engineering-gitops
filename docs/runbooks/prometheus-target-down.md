# Prometheus Target Down

## Symptoms
Prometheus UI /targets shows DOWN; gaps in graphs; Alertmanager silent if not configured (lab gap).

## First 60 Seconds (READ-ONLY)
```bash
kubectl get pods -n monitoring   # VMware
kubectl get pods -n observability # AWS
kubectl get servicemonitor -A
kubectl get endpoints -n platform-lab
```

## Triage
1. Is the **scrape target** the app (`/metrics`) or kube-system/control-plane?
2. Known control-plane scrape failures are **not** application incidents (**Observed** where documented).
3. Check ServiceMonitor selectors vs Pod/Service labels.
4. Port and path: Project 1 app path **`/metrics`**.
5. NetworkPolicy may block scrape on VMware (**Observed**).

## Diagnosis
| Check | Meaning |
|---|---|
| Service exists, no Endpoints | Readiness / selector |
| Endpoints OK, target DOWN | scrape path/port/NP/TLS |
| KSM/node-exporter DOWN | observability plane |

## Safe Remediation
Fix labels/ServiceMonitor/NetworkPolicy via **Git**, not one-off UI edits. Restart Prometheus only if approved and Git-aligned.

## Verification
Target UP; query returns series; Argo Application Healthy.

## Related
[kube-observability-troubleshooting.md](./kube-observability-troubleshooting.md) · [networkpolicy-troubleshooting.md](./networkpolicy-troubleshooting.md)
