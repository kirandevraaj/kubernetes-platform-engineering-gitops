# AWS Lightweight Observability

**Date:** 2026-09-25  
**GitOps Application:** `platform-observability-aws`  
**Commit introducing stack:** `a37bc924530d4a2ae0f04e32264787534e729c54`

---

## 1. Objective

Establish the first AWS observability path:

```text
platform-lab (/metrics) → Prometheus → Grafana
```

This milestone deploys **only** Prometheus and Grafana via Argo CD. It does **not** install a full Kubernetes monitoring suite.

## 2. Why We Upgraded the Worker Nodes

The prior capacity analysis on **2 × t3.small** showed abundant CPU but constrained **actual memory** (~64% used) and **pod density** (~4 free slots). Worker nodes were scaled to **2 × t3.medium** (`862588e`) before this install to provide memory and pod-slot headroom for a minimal Prom+Grafana pair.

## 3. Current EKS Capacity

Measured on context `platform-lab-aws` immediately **before** observability deploy:

| Metric | Value |
|---|---|
| Nodes | 2 × t3.medium, Ready, no MemoryPressure |
| CPU allocatable (cluster) | ~3.86 cores |
| Memory allocatable (cluster) | ~6588 Mi |
| Pod capacity | 34 |
| Actual CPU usage | ~76m (~2%) |
| Actual memory usage | ~1264 Mi (~19%) |
| Running pods | 18 |

## 4. Architecture

```text
Internet
   │
   ▼
 AWS ALB  ──────────────────────────►  platform-lab :8000
                                          │
                                          │ scrape /metrics (30s)
                                          ▼
                                   Prometheus (ClusterIP)
                                   namespace: observability
                                          │
                                          │ datasource query
                                          ▼
                                   Grafana (ClusterIP)
                                   namespace: observability
                                          ▲
                                          │
                              kubectl port-forward :3000
                              (localhost only; no ALB)
```

Application traffic and observability traffic are separate paths. Grafana is **not** on the ALB.

## 5. Prometheus

| Item | Value |
|---|---|
| Chart | `prometheus-community/prometheus` |
| Chart version | **29.33.0** (app `v3.14.0`) |
| Namespace | `observability` |
| Release name | `prometheus` |
| Replicas | 1 |
| Service | `prometheus-server` (ClusterIP) |
| Retention | **6h** |
| Storage | **emptyDir** `sizeLimit: 1Gi` (no PVC; no EBS CSI) |

Disabled sub-charts: Alertmanager, node-exporter, kube-state-metrics, Pushgateway.

## 6. Grafana

| Item | Value |
|---|---|
| Chart | `grafana/grafana` |
| Chart version | **10.5.15** (app `12.3.1`) |
| Namespace | `observability` |
| Release name | `grafana` |
| Replicas | 1 |
| Service | `grafana` (**ClusterIP only**) |
| Database | embedded **SQLite** (no external DB) |
| Auth | **anonymous Viewer**; login form disabled; no password in Git |

Access:

```powershell
kubectl -n observability port-forward svc/grafana 3000:80
# open http://127.0.0.1:3000
```

## 7. Scrape Configuration

Broad default Kubernetes scrape jobs are **disabled**.

Active jobs:

| Job | Target | Path | Interval |
|---|---|---|---|
| `prometheus` | self (`localhost:9090`) | `/metrics` | chart default |
| `platform-lab` | endpoints of Service `platform-lab` in `platform-lab` | `/metrics` | **30s** |

Verified live metrics from the app include: `http_requests_total`, `process_resident_memory_bytes`, `process_cpu_seconds_total`, and related process/HTTP families.

## 8. Storage Decision

| Option | Outcome |
|---|---|
| `gp2` StorageClass | Present (`kubernetes.io/aws-ebs`) but **EBS CSI is not installed**; PVC binding would require new infrastructure |
| emptyDir (chosen) | Used for Prometheus with **1Gi sizeLimit**; history lost on pod recreate — acceptable for this lab |

No PVC was created. Grafana persistence is disabled (SQLite on emptyDir/ephemeral).

## 9. Resource Requests and Limits

| Component | CPU request | Memory request | Memory limit |
|---|---|---|---|
| Prometheus server | 100m | 384Mi | 512Mi |
| Grafana | 50m | 256Mi | 512Mi |

Soft preferred anti-affinity spreads Prometheus and Grafana across the two nodes when possible (observed: Prom on one node, Grafana on the other).

## 10. GitOps / Argo CD

| Object | Path |
|---|---|
| AppProject | `gitops/projects/platform-observability-aws.yaml` |
| Application | `gitops/applications/platform-observability-aws.yaml` |
| Prometheus values | `observability/aws/values-prometheus.yaml` |
| Grafana values | `observability/aws/values-grafana.yaml` |
| Dashboard ConfigMap | `observability/aws/dashboards/` |

Application settings: automated sync, prune, selfHeal, `CreateNamespace=true`.

Helm repos allowed: prometheus-community + grafana (minimal AppProject sourceRepos).

Deployment path:

```text
Git main → Argo CD Application platform-observability-aws → Helm releases in observability
```

`platform-lab-aws` / `platform-lab-local` were **not** modified.

## 11. Access Model

| Surface | Exposure |
|---|---|
| platform-lab | Internet via existing ALB |
| Prometheus | ClusterIP + `kubectl port-forward` |
| Grafana | ClusterIP + `kubectl port-forward` + anonymous Viewer |

**No** public Grafana endpoint, **no** additional ALB, **no** LoadBalancer/NodePort/Ingress for Grafana.

## 12. Validation

| Check | Result |
|---|---|
| Argo `platform-observability-aws` | Synced / Healthy |
| Prometheus `/-/ready` | Ready |
| Targets | `platform-lab` **up** (both pods), `prometheus` **up** |
| Query `up{job="platform-lab"}` | 1 |
| Query `sum(rate(http_requests_total{job="platform-lab"}[5m]))` | success (non-empty) |
| Grafana `/api/health` | database ok, version 12.3.1 |
| Datasource | Prometheus → `http://prometheus-server.observability.svc.cluster.local` |
| Dashboard | `platform-lab AWS (lightweight)` (`platform-lab-aws-lightweight`) |
| Datasource proxy query | `min(up{job="platform-lab"})` → **1** |
| platform-lab `/health` | HTTP 200 |
| platform-lab `/version` | `0.1.4` |
| Forbidden components | none installed |

## 13. Measured Resource Footprint

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Cluster CPU usage (sum of nodes) | ~76m | ~69m | ~noise |
| Cluster memory usage | ~1264 Mi | ~1788 Mi | **+~524 Mi** |
| Memory utilization vs allocatable | ~19% | ~27% | +8 pp |
| Pod count | 18 | 20 | +2 |

Observability pod usage (`kubectl top`):

| Pod | CPU | Memory |
|---|---:|---:|
| `prometheus-server` | ~4m | ~35 Mi |
| `grafana` | ~3m | ~171 Mi |
| **Combined** | **~7m** | **~206 Mi** |

Requests remain higher than RSS (especially Prometheus); that is intentional headroom for scrape growth within the 512Mi limit.

## 14. Current Limitations

- No node/kubelet metrics (no node-exporter / cAdvisor scrape)
- No Kubernetes object metrics (no kube-state-metrics)
- No alerting (no Alertmanager)
- No traces/logs (no OTel / Loki / Tempo / Jaeger)
- Prometheus history is ephemeral (emptyDir)
- Grafana is localhost-only via port-forward
- Scrapes are limited to `platform-lab` + Prometheus self

## 15. Future Expansion Criteria

Post-deploy headroom (approximate):

| Resource | Approx remaining |
|---|---|
| Allocatable memory unused | ~6588 − 1788 ≈ **4800 Mi** |
| Free pod slots | 34 − 20 = **14** |
| CPU | still largely idle |

**Analysis only — not deployed in this milestone:**

| Component | Appears capacity-feasible? | Notes |
|---|---|---|
| kube-state-metrics | Likely | small Deployment; re-measure after add |
| node-exporter | Likely | DaemonSet costs **2** pods; memory still ample on t3.medium |
| Alertmanager | Likely | small; only if alerting workflow is defined |
| OpenTelemetry Collector | Conditional | useful when traces/logs exist; avoid overlapping Prom for metrics |

Re-measure `kubectl top nodes/pods` and free pod slots before any expansion. Do **not** install kube-prometheus-stack on this cluster without a fresh capacity review.
