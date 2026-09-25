# Grafana Platform/SRE Dashboard

**Date:** 2026-09-25  
**Commit theme:** Cross-environment Platform/SRE dashboards  
**Application version (unchanged):** `0.1.4` · digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## 1. Objective

Turn existing Prometheus telemetry into operational Platform/SRE dashboards so an engineer can answer, in about 30 seconds:

1. How healthy is the cluster?
2. Are nodes under CPU/memory pressure?
3. How many pods are running?
4. Is the application deployment healthy?
5. Is the HPA scaling?
6. Are desired and available replicas aligned?
7. Is application traffic increasing?
8. Is application CPU/memory increasing?
9. Is Prometheus scraping the expected targets?
10. Is the monitoring stack itself healthy?

Equivalent conceptual dashboards exist for **AWS** and **VMware**. PromQL differs only where labels/jobs differ.

## 2. Dashboard Architecture

```text
platform-lab /metrics ───────┐
                             │
kube-state-metrics ──────────┼──→ Prometheus → Grafana (Platform/SRE dashboards)
                             │
node-exporter ───────────────┘

Separately (not on these dashboards as a control path):
Metrics Server → HPA → platform-lab replicas
```

Prometheus does **not** drive HPA. kube-state-metrics exposes HPA *object state* for visualization only.

Existing application dashboards remain separate:

| Environment | Application dashboard (kept) | Platform/SRE dashboard (this milestone) |
|---|---|---|
| AWS | `platform-lab AWS (lightweight)` | **Kubernetes Platform AWS** |
| VMware | `platform-lab` (existing) | **Kubernetes Platform VMware** |

## 3. Data Sources

| Env | Grafana datasource UID | Prometheus flavour |
|---|---|---|
| AWS | `prometheus` | Standalone `prometheus` chart · ns `observability` |
| VMware | `prometheus` | kube-prometheus-stack · ns `monitoring` |

GitOps provisioning:

| Env | Path | Argo Application |
|---|---|---|
| AWS | `observability/aws/dashboards/` | `platform-observability-aws` |
| VMware | `observability/dashboards/` | `platform-lab-observability` |

## 4. Cluster Overview Panels

| Panel | Purpose | PromQL (verified) |
|---|---|---|
| Nodes UP | Worker/node-exporter coverage | `count(up{job="node-exporter"} == 1)` |
| Pods Running | Cluster running pods | `count(kube_pod_status_phase{phase="Running"} == 1)` |
| Cluster CPU util | Avg non-idle CPU | `1 - avg(rate(node_cpu_seconds_total{job="node-exporter",mode="idle"}[5m]))` |
| Cluster memory util | Used = Total−Available | `1 - (sum(node_memory_MemAvailable_bytes{job="node-exporter"}) / sum(node_memory_MemTotal_bytes{job="node-exporter"}))` |
| Targets UP / DOWN | Scrape health summary | `count(up == 1)` · `count(up == 0) or vector(0)` |
| App / Prometheus UP | Key target health | `min(up{job="platform-lab"})` · env-specific Prometheus job |

Units: `percentunit` for utilization stats.

## 5. Node Health Panels

Per-node time series (filtered by `$node` variable):

| Panel | PromQL |
|---|---|
| Node CPU utilization | `1 - avg by (instance[, node]) (rate(node_cpu_seconds_total{job="node-exporter",mode="idle",instance=~"$node"}[5m]))` |
| Node memory utilization | `1 - (node_memory_MemAvailable_bytes{job="node-exporter",instance=~"$node"} / node_memory_MemTotal_bytes{job="node-exporter",instance=~"$node"})` |
| Root filesystem utilization | `1 - (node_filesystem_avail_bytes{...,mountpoint="/",...} / node_filesystem_size_bytes{...,mountpoint="/",...})` |

AWS legends prefer `{{node}} ({{instance}})`. VMware uses `{{instance}}` (node label not consistently present on those series).

## 6. Kubernetes State Panels

Scoped with variables `$namespace` / `$deployment` (defaults `platform-lab`):

| Panel | PromQL |
|---|---|
| Desired replicas | `kube_deployment_spec_replicas{namespace="$namespace",deployment="$deployment"}` |
| Available replicas | `kube_deployment_status_replicas_available{...}` |
| App pod count | `count(kube_pod_info{namespace="$namespace"})` |
| HPA min/max/current/desired | `kube_horizontalpodautoscaler_spec_*` / `status_*` with `horizontalpodautoscaler="$deployment"` |
| Replica gap | desired − available |
| Desired vs available (timeseries) | both deployment metrics |
| HPA scaling view | HPA current, desired, min, max + deploy available |

## 7. Application Panels

| Panel | PromQL |
|---|---|
| App availability | `min(up{job="platform-lab",namespace="$namespace"})` |
| HTTP request rate | `sum(rate(http_requests_total{job="platform-lab",namespace="$namespace"}[5m]))` |
| Process CPU | `rate(process_cpu_seconds_total{job="platform-lab",namespace="$namespace"}[5m])` |
| Process memory | `process_resident_memory_bytes{job="platform-lab",namespace="$namespace"}` |

## 8. Prometheus Health Panels

| Panel | PromQL |
|---|---|
| KSM / node-exporter / platform-lab / self | `up` filtered by job |
| Target up by job | `sum by (job) (up)` |
| Scrape duration by job | `avg by (job) (scrape_duration_seconds)` |
| Samples scraped by job | `sum by (job) (scrape_samples_scraped)` |

`scrape_series_added` exists but is usually `0` at steady state — not used as a primary health signal.

## 9. HPA Visualization

Panel **HPA current vs desired (scaling view)** overlays:

- HPA current replicas
- HPA desired replicas
- Deployment available replicas
- HPA min / max

Prior load-test history may already have aged out of Prometheus retention (AWS retention is **6h** emptyDir). The panel is ready for the next controlled load test; this milestone does **not** re-run load or change HPA.

## 10. Variables

| Variable | Source | Default |
|---|---|---|
| `namespace` | `label_values(kube_deployment_spec_replicas, namespace)` | `platform-lab` |
| `deployment` | deployments in `$namespace` | `platform-lab` |
| `node` | `label_values(up{job="node-exporter"}, instance)` multi + All | All (`.*`) |

## 11. PromQL Reference

### AWS-only differences

| Topic | AWS |
|---|---|
| Prometheus self job | `job="prometheus"` |
| node-exporter job | `job="node-exporter"` |
| Target count (validated) | **6 UP** |

### VMware-only differences

| Topic | VMware |
|---|---|
| Prometheus self job | `job="kube-prometheus-stack-prometheus"` |
| node-exporter job | `job="node-exporter"` (same name) |
| Extra scrape jobs | kubelet, coredns, apiserver, … (stack default) |
| Targets (validated) | **22 UP**, **6 DOWN** (control-plane endpoints often fail in lab — expected noise) |

Shared application / KSM metric names were verified identical for `platform-lab` and HPA objects.

## 12. AWS Dashboard

| Field | Value |
|---|---|
| Title | Kubernetes Platform AWS |
| UID | `kubernetes-platform-aws` |
| ConfigMap | `kubernetes-platform-aws-grafana-dashboard` |
| Namespace | `observability` |
| Panels | **36** (+ 5 section rows) |
| Sections | Cluster Overview · Node Health · Kubernetes State · Application · Prometheus Health |

## 13. VMware Dashboard

| Field | Value |
|---|---|
| Title | Kubernetes Platform VMware |
| UID | `kubernetes-platform-vmware` |
| ConfigMap | `kubernetes-platform-vmware-grafana-dashboard` |
| Namespace | `monitoring` |
| Panels | **36** (+ 5 section rows) |
| Sections | Same five sections as AWS |

## 14. Cross-Environment Differences

| Dashboard Capability | VMware | AWS | Difference type |
|---|---|---|---|
| Cluster overview | Yes | Yes | Same concept |
| Node CPU | Yes (3 nodes) | Yes (2 workers) | Infrastructure (node count) |
| Node memory | Yes | Yes | Label legend (`instance` vs `node`) |
| Filesystem | Yes | Yes | fstype `ext4` vs `xfs` |
| Pod count | Yes | Yes | Same metrics |
| Deployment replicas | Yes | Yes | Same metrics |
| HPA state | Yes | Yes | Same metrics |
| Application request rate | Yes | Yes | Same `http_requests_total` |
| Application CPU/memory | Yes | Yes | Same process_* metrics |
| Application availability | Yes | Yes | Same `up{job="platform-lab"}` |
| Prometheus target health | Yes (many jobs) | Yes (4 jobs) | Intentional architecture (stack vs lightweight) |

## 15. Validation Results

Metric families were queried live before panel authoring (AWS via in-pod Prometheus API; VMware via port-forward).

| Check | AWS | VMware |
|---|---|---|
| Deployment desired/available = 2/2 | Yes | Yes |
| HPA min/current/desired/max = 2/2/2/4 | Yes | Yes |
| Node CPU/mem/fs series present | 2 instances | 3 instances |
| App HTTP rate / process metrics | Yes | Yes |
| scrape_duration_seconds / scrape_samples_scraped | Yes | Yes |

## 16. Current Limitations

- No Alertmanager / alerting rules on these dashboards
- AWS Prometheus retention **6h** — historical HPA load experiments may not still be visible
- VMware shows some DOWN targets for control-plane scrapes; treated as lab noise, not application failure
- No logs/traces correlation (Loki/Tempo not installed)

## 17. Future Enhancements

1. Recording rules for cluster CPU/memory to cheapen overview queries
2. Alerting thresholds wired to Alertmanager only after capacity review
3. Optional dashboard link between app and platform views
4. Longer retention / remote write only if operational need outweighs cost
