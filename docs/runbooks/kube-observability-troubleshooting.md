# Kube Observability Troubleshooting (KSM / node-exporter / Prometheus)

| Component | Role |
|---|---|
| kube-state-metrics | Kubernetes **object** state metrics |
| node-exporter | Node **OS** metrics |
| Prometheus | Scrape, store, query |
| Grafana | Visualize |
| Metrics Server | Resource metrics API (HPA/`kubectl top`) — separate runbook |

## First 60 Seconds (READ-ONLY)
```bash
kubectl get pods -n monitoring      # VMware
kubectl get pods -n observability   # AWS
# Prometheus targets UI or API — confirm KSM / node-exporter UP
```

## Triage
1. Is the gap in **object** metrics (KSM), **node** metrics (exporter), or **scrape** (Prometheus)?
2. DaemonSet node-exporter missing on a node?
3. ServiceMonitor/PodMonitor selectors?

## Safe Remediation
GitOps fix for labels/resources; see [prometheus-target-down.md](./prometheus-target-down.md), [grafana-unavailable.md](./grafana-unavailable.md).

## Verification
Targets UP; sample queries return data; Argo observability Application Healthy.
