# Kubernetes Platform Observability

**Date:** 2026-09-25  
**AWS GitOps Applications:** `platform-observability-aws`, `platform-k8s-metrics-aws`  
**Scope:** Bring AWS Kubernetes-level metrics (kube-state-metrics + node-exporter) to the same conceptual level as VMware, without installing a full monitoring platform.

---

## 1. Objective

Add Kubernetes state metrics and node metrics on AWS EKS, integrate them with the existing standalone Prometheus, and validate Grafana queries — while keeping Metrics Server as the sole HPA resource-metrics path.

```text
                   Application
                       │
                   /metrics
                       │
                       ▼
                    Prometheus
                       ▲
             ┌─────────┴─────────┐
             │                   │
   kube-state-metrics       node-exporter
             │                   │
     Kubernetes state       Node metrics
```

## 2. Why Metrics Server, Prometheus, kube-state-metrics and node-exporter Are Different

| Component | What it provides | Used for in this lab |
|---|---|---|
| **Metrics Server** | Short-window CPU/memory usage of pods/nodes via the Metrics API | **HPA** resource metrics only |
| **Prometheus** | Time-series store + scrape engine | Historical/observability queries and Grafana |
| **kube-state-metrics** | Kubernetes API object state as Prometheus metrics | Desired vs available replicas, HPA status objects, pod/deployment inventory |
| **node-exporter** | Host OS/hardware metrics from each node | Node CPU, memory, filesystem, network |

`kube-state-metrics` is **not** a replacement for Metrics Server.  
`node-exporter` is **not** a replacement for Metrics Server.  
Prometheus does **not** drive HPA in this project.

## 3. VMware Observability

VMware (`ckad-lab`) uses **kube-prometheus-stack** in namespace `monitoring`.

| Component | Name | Status (read-only check) |
|---|---|---|
| Prometheus | `prometheus-kube-prometheus-stack-prometheus-0` | Running |
| Grafana | `kube-prometheus-stack-grafana` | Running (MetalLB LB) |
| kube-state-metrics | Deployment `kube-prometheus-stack-kube-state-metrics` · image `registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.20.0` · 1/1 | Healthy |
| node-exporter | DaemonSet `kube-prometheus-stack-prometheus-node-exporter` · image `quay.io/prometheus/node-exporter:v1.12.1-distroless` · 3/3 (ctrl + 2 workers) | Healthy |
| Scrape mechanism | Prometheus Operator **ServiceMonitor**s | Operator-managed |

**Do not** install a second kube-state-metrics or node-exporter on VMware — they already exist and are healthy.

## 4. AWS Observability

AWS uses a **lightweight** stack (no kube-prometheus-stack, no Prometheus Operator):

| Layer | Application | Components |
|---|---|---|
| Core | `platform-observability-aws` | Prometheus chart `29.33.0` (app `v3.14.0`) + Grafana chart `10.5.15` (app `12.3.1`) |
| K8s metrics | `platform-k8s-metrics-aws` | kube-state-metrics + prometheus-node-exporter |
| HPA path | (cluster addon / kube-system) | Metrics Server — unchanged |

Namespace for observability workloads: `observability`.

## 5. kube-state-metrics

| Item | Value |
|---|---|
| Chart | `prometheus-community/kube-state-metrics` |
| Chart version | **8.5.0** |
| App version | **2.20.0** |
| Replicas | **1** |
| Service | ClusterIP `:8080` (port name `http`) |
| Resources | requests `50m` / `64Mi`; limits `200m` / `128Mi` |

**Measures:** Kubernetes object state from the API (deployments, pods, HPA specs/status, nodes, services, …).

**Does not measure:** container CPU/memory usage rates (that is Metrics Server / cAdvisor territory) or host CPU/filesystem (node-exporter).

**Focused collectors enabled:** `nodes`, `pods`, `deployments`, `replicasets`, `services`, `endpointslices`, `horizontalpodautoscalers`, `statefulsets`.

Example metrics verified against `platform-lab`:

- `kube_deployment_spec_replicas`
- `kube_deployment_status_replicas_available`
- `kube_horizontalpodautoscaler_spec_min_replicas` / `_max_replicas`
- `kube_horizontalpodautoscaler_status_current_replicas` / `_desired_replicas`
- `kube_pod_info`

## 6. node-exporter

| Item | Value |
|---|---|
| Chart | `prometheus-community/prometheus-node-exporter` |
| Chart version | **4.57.0** |
| App version | **1.12.1** |
| Model | DaemonSet (one pod per node) |
| Expected AWS pods | **2** (2 × t3.medium workers) |
| Service | ClusterIP `:9100` (port name `metrics`) |
| Resources | requests `25m` / `32Mi`; limits `100m` / `64Mi` |

**Host-level access (official chart defaults — documented intentionally):**

| Setting | Value | Why |
|---|---|---|
| `hostNetwork` | `true` | Accurate host network interface metrics |
| `hostPID` | `true` | Host process / load metrics |
| `hostRootFsMount` | enabled | Host filesystem stats |
| `/host/proc`, `/host/sys` | mounted | Kernel/CPU stats |
| `privileged` | **false** | Not required |
| `runAsNonRoot` | uid `65534` | Hardened default |

## 7. Prometheus Scrape Architecture

```text
application /metrics
        \
kube-state-metrics → Prometheus → Grafana
        /
node-exporter
```

Jobs (standalone Prometheus `extraScrapeConfigs`, **no** ServiceMonitor/PodMonitor):

| Job | Discovery | Expected targets |
|---|---|---|
| `prometheus` | self | 1 |
| `platform-lab` | endpoints SD in `platform-lab` | 2 (app replicas) |
| `kube-state-metrics` | endpoints SD in `observability` | 1 |
| `node-exporter` | endpoints SD in `observability` (per endpoint, not ClusterIP only) | 2 (one per node) |

Scrape interval: **30s**.

## 8. Metrics Server vs Prometheus

```text
Metrics Server  →  Metrics API  →  HPA (CPU target)
Prometheus      →  TSDB        →  Grafana / historical analysis
```

Changing HPA behaviour requires Metrics Server (and HPA objects), not Prometheus scrape config.  
Observability dashboards use Prometheus only.

## 9. Resource Impact

Measured on context `platform-lab-aws` (2 × t3.medium).

### Before exporters

| Metric | Value |
|---|---|
| Node memory | ~1515 Mi + ~532 Mi ≈ **2047 Mi** |
| Node CPU | ~59m + ~51m ≈ **110m** |
| Pod count | **20** |
| Prometheus | ~5m / **36 Mi** |
| Grafana | ~5m / **153 Mi** |
| Prometheus targets | **3** (2× platform-lab + self) |

### After exporters

| Metric | Value |
|---|---|
| Node memory | ~1595 Mi + ~576 Mi ≈ **2171 Mi** (~**+124 Mi** cluster-wide) |
| Node CPU | ~52m + ~40m ≈ **92m** (within noise; no meaningful CPU pressure) |
| Pod count | **23** (+1 kube-state-metrics + 2 node-exporter) |
| kube-state-metrics | ~1m / **12–13 Mi** |
| node-exporter (×2) | ~1m / **3–7 Mi** each |
| Prometheus | ~9m / **47 Mi** (slight rise after additional series) |
| Grafana | ~3m / **171 Mi** |
| Prometheus targets | **6** (all UP) |

Observability exporter footprint is small relative to t3.medium headroom. node-exporter runs once per node as expected.

## 10. Validation Results

| Check | Result |
|---|---|
| Targets before | **3** |
| Targets after | **6** |
| `kube-state-metrics` | **UP** (1 target) |
| `node-exporter` | **UP** on both workers (`ip-10-50-41-156`, `ip-10-50-52-64`) |
| `platform-lab` / Prometheus self | remain **UP** |
| Sample KSM metrics | `kube_deployment_spec_replicas{deployment="platform-lab"}=2`, `kube_deployment_status_replicas_available=2`, HPA current/desired=2, min=2, max=4, `count(kube_pod_info)=23` |
| Sample node metrics | `node_memory_MemTotal_bytes`, `node_memory_MemAvailable_bytes`, `node_cpu_seconds_total`, `node_filesystem_avail_bytes{mountpoint="/"}` present per node |
| Grafana dashboards | **platform-lab AWS (lightweight)** + **Kubernetes Platform AWS** (`uid: kubernetes-platform-aws`) |
| Argo CD | `platform-k8s-metrics-aws`, `platform-observability-aws`, `platform-lab-aws` → Synced/Healthy |
| ALB | `/health` 200, `/version` 0.1.4, digest unchanged |

Note: kube-state-metrics scrape uses `honor_labels: true` so object `namespace` / `pod` labels are preserved (not rewritten to `exported_*`).

## 11. VMware vs AWS Comparison

| Capability | VMware | AWS |
|---|---|---|
| Prometheus | kube-prometheus-stack (Operator) | Standalone prometheus chart |
| Grafana | kube-prometheus-stack (MetalLB LB) | Standalone grafana chart (ClusterIP + port-forward) |
| Metrics Server | Yes (HPA) | Yes (HPA) |
| kube-state-metrics | Via kube-prometheus-stack | Standalone chart via `platform-k8s-metrics-aws` |
| node-exporter | Via kube-prometheus-stack (3 nodes) | Standalone chart DaemonSet (2 workers) |
| Application metrics | ServiceMonitor → Prometheus | `extraScrapeConfigs` endpoints SD |
| HPA | Yes | Yes |
| Ingress / LB | ingress-nginx + MetalLB | AWS ALB (LBC) |
| Node count | 3 (1 CP + 2 workers) | 2 workers (EKS managed) |
| Metrics collection method | Operator ServiceMonitors | Static/extra scrape + k8s_sd |

Same architectural concepts; environment-specific implementation.

## 12. Current Limitations

Not installed (intentionally):

- Alertmanager
- OpenTelemetry
- Loki
- Tempo
- Jaeger
- kube-prometheus-stack on AWS

## 13. Future Expansion Criteria

Before adding more components, measure:

1. Sustained memory/CPU headroom on both workers after exporters + app peak
2. Whether alerting requires Alertmanager vs external notification
3. Whether logs/traces are needed for an incident the metrics path cannot explain
4. Pod-slot remaining headroom (current capacity 34)

Do not grow the stack to match VMware feature-for-feature without a capacity and operational need.
