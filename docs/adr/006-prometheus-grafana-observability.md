# ADR 006: Prometheus + Grafana observability

- **Status:** Accepted

## Decision

Prometheus + Grafana for metrics UI; kube-state-metrics + node-exporter for object/node metrics; Metrics Server separately for HPA/`kubectl top`.

## Distinction

| Tool | Role |
|---|---|
| Metrics Server | Resource metrics API |
| Prometheus | Scrape/store/query |
| Grafana | Dashboards |
| KSM | Kubernetes object state |
| node-exporter | Node OS metrics |

## Evidence

VMware `monitoring` Healthy · AWS `observability` — see [aws-observability-degraded-final-state.md](../portfolio/aws-observability-degraded-final-state.md)
