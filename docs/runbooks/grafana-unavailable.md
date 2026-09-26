# Grafana Unavailable

Separate **VMware** (`monitoring`) and **AWS** (`observability`).

## Symptoms
UI unreachable; Pod CrashLoop/OOMKilled/Pending; datasource errors.

## First 60 Seconds (READ-ONLY)
```bash
# VMware
kubectl get pods,svc -n monitoring -l app.kubernetes.io/name=grafana
kubectl describe pod -n monitoring -l app.kubernetes.io/name=grafana
# AWS
kubectl get pods,svc -n observability -l app.kubernetes.io/name=grafana
```

## Observed Project 1 (VMware)
Memory limit too low → OOM → GitOps resource increase → stable Grafana. See [grafana-oom.md](../postmortems/grafana-oom.md).

## AWS note (Observed during Section 26 regression)
A second Grafana Pod may sit **Pending** while one replica **Running 2/2**, leaving Argo Application **Degraded**. Existing UI may still work — triage Pending (resources/scheduling) without deleting healthy Pod casually.

## Diagnosis
- Resources / OOM history
- Service type (LB vs ClusterIP) per environment
- Prometheus datasource URL
- Dashboard provisioning ConfigMaps

## Safe Remediation
Raise limits / fix scheduling via GitOps. Do not store admin passwords in runbook evidence.

## Verification
Pod Ready; login UI; datasource OK; Argo Healthy.

## Related
[prometheus-target-down.md](./prometheus-target-down.md)
