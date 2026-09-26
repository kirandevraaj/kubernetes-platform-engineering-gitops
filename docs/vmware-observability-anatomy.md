# VMware Kubernetes Observability Anatomy

**Date:** 2026-09-26  
**Exercise type:** Read-only learning lab  
**Cluster context:** `ckad-lab` (VMware / on-prem kubeadm)  
**No cluster changes were made during this exploration.**

---

## 1. Environment

| Item | Value |
|---|---|
| kubectl context | `ckad-lab` (current) |
| API server | `https://192.168.56.10:6443` |
| Kubernetes | `v1.31.14` |
| Nodes | `k8s-ctrl-01` `192.168.56.10`, `k8s-worker-01` `192.168.56.11`, `k8s-worker-02` `192.168.56.12` |
| Observability stack | **kube-prometheus-stack** in namespace `monitoring` |
| Application | `platform-lab` in namespace `platform-lab` |
| Grafana UI | http://192.168.56.201 (MetalLB LoadBalancer) |

This is **not** AWS. AWS uses a separate lightweight Prometheus/Grafana design.

---

## 2. Components

| Component | Namespace | Resource | Pods | Image | Service | Port | How Prometheus finds it |
|---|---|---|---|---|---|---|---|
| **Prometheus** | `monitoring` | StatefulSet pod `prometheus-kube-prometheus-stack-prometheus-0` | 1 (+ sidecar) | `quay.io/prometheus/prometheus:v3.14.0-distroless` | `kube-prometheus-stack-prometheus` ClusterIP | 9090 | Self + Operator-managed scrape configs |
| **Grafana** | `monitoring` | Deployment | 1 | `grafana/grafana:13.2.2-distroless` | `kube-prometheus-stack-grafana` **LoadBalancer** `192.168.56.201` | 80 | Queried as client of Prometheus (not scraped for app panels) |
| **kube-state-metrics** | `monitoring` | Deployment | **1** | `registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.20.0` | `kube-prometheus-stack-kube-state-metrics` ClusterIP | 8080 | **ServiceMonitor** → job `kube-state-metrics` |
| **node-exporter** | `monitoring` | DaemonSet | **3** (1/node) | `quay.io/prometheus/node-exporter:v1.12.1-distroless` | `kube-prometheus-stack-prometheus-node-exporter` ClusterIP | 9100 | **ServiceMonitor** → job `node-exporter` (3 endpoints) |
| **Metrics Server** | `kube-system` | Deployment | **1** | `registry.k8s.io/metrics-server/metrics-server:v0.9.0` | `metrics-server` ClusterIP | 443 | **Not scraped by Prometheus** in this lab |
| **platform-lab** | `platform-lab` | Deployment | **2** | app image digest `0.1.4` | `platform-lab` ClusterIP | 8000 (`http`) | **ServiceMonitor** `platform-lab` → job `platform-lab` |
| Prometheus Operator | `monitoring` | Deployment | 1 | (operator) | ClusterIP | 443 | Watches ServiceMonitors / Prometheus CR |

**Scrape mechanism on VMware:** Prometheus Operator reads `ServiceMonitor` CRs and generates scrape configs. There is no hand-written `extraScrapeConfigs` like on AWS.

Verified ServiceMonitors include:

- `platform-lab/platform-lab` (path `/metrics`, port `http`, interval `30s`)
- `monitoring/...-kube-state-metrics`
- `monitoring/...-prometheus-node-exporter`
- plus kubelet, coredns, apiserver, etc. from the stack

---

## 3. Application Metrics

**Who produces them?** The FastAPI `platform-lab` process itself, via its Prometheus client instrumentation, exposed at `:8000/metrics`.

**Live inspection (read-only port-forward to `svc/platform-lab`):**

| Metric | TYPE | Example labels | Observed |
|---|---|---|---|
| `http_requests_total` | **counter** | `handler`, `method`, `status` | e.g. `handler="/health",status="200"` → 2516 |
| `process_cpu_seconds_total` | **counter** | (process-level) | e.g. `22.62` seconds cumulative |
| `process_resident_memory_bytes` | **gauge** | (process-level) | e.g. `~56 MiB` |

### Why `rate()` matters

- Counters only go up (or reset on restart). Raw values are not “requests per second”.
- `rate(http_requests_total[1m])` estimates per-second increase over the window.
- Gauges like RSS are used as-is (or summed across pods).

### Labels that matter

On the scraped series in Prometheus (after ServiceMonitor scrape), useful labels include:

- `job="platform-lab"`
- `namespace="platform-lab"`
- `pod=<pod-name>`
- `instance=<pod-ip>:8000`
- plus original `handler` / `method` / `status` from the app

### Endpoints

```text
Service platform-lab → Endpoints 10.244.118.107:8000, 10.244.118.125:8000
```

Prometheus scrapes **both** endpoints → two `up{job="platform-lab"}` targets.

---

## 4. node-exporter

**Who produces them?** Linux kernel/OS stats, exported by node-exporter running with host access (`hostNetwork: true`, `hostPID: true`, host fs mounts).

**Why DaemonSet?** Every node has its own CPU, memory, and disks. One exporter pod per node is the correct model.

| Node | Pod IP (host network) | Status |
|---|---|---|
| k8s-ctrl-01 (192.168.56.10) | 192.168.56.10:9100 | Running |
| k8s-worker-01 (192.168.56.11) | 192.168.56.11:9100 | Running |
| k8s-worker-02 (192.168.56.12) | 192.168.56.12:9100 | Running |

Service endpoints list all three: `192.168.56.10:9100,192.168.56.11:9100,192.168.56.12:9100`.

### Verified metrics

| Metric | TYPE | Units | Meaning |
|---|---|---|---|
| `node_cpu_seconds_total` | counter | seconds | CPU time spent in modes (`idle`, `user`, `system`, …) per CPU |
| `node_memory_MemTotal_bytes` | gauge | bytes | Total physical memory |
| `node_memory_MemAvailable_bytes` | gauge | bytes | Estimate of memory available for new workloads |
| `node_filesystem_avail_bytes` | gauge | bytes | Free space on a mount (e.g. `mountpoint="/"`) |

### How Grafana turns these into percentages

```text
CPU util ≈ 1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))
Memory util ≈ 1 - (MemAvailable / MemTotal)
Filesystem util ≈ 1 - (Avail / Size) for mountpoint="/"
```

These are **not** Metrics Server metrics. They are host-level observability series for history and dashboards.

---

## 5. kube-state-metrics

**Who produces them?** kube-state-metrics watches the **Kubernetes API** and converts object *desired/actual state* into Prometheus metrics. It does **not** measure container CPU/memory usage.

**Deployment:** 1 replica · Service ClusterIP `:8080` · Endpoint `10.244.36.214:8080`

### Verified metrics (live `/metrics`)

| Metric | Object | Useful labels | Live value (platform-lab) |
|---|---|---|---|
| `kube_deployment_spec_replicas` | Deployment.spec.replicas | `namespace`, `deployment` | **2** |
| `kube_deployment_status_replicas_available` | Deployment.status.availableReplicas | same | **2** |
| `kube_horizontalpodautoscaler_spec_min_replicas` | HPA.spec.minReplicas | `namespace`, `horizontalpodautoscaler` | **2** |
| `kube_horizontalpodautoscaler_spec_max_replicas` | HPA.spec.maxReplicas | same | **4** |
| `kube_horizontalpodautoscaler_status_current_replicas` | HPA.status.currentReplicas | same | **2** |
| `kube_horizontalpodautoscaler_status_desired_replicas` | HPA.status.desiredReplicas | same | **2** |
| `kube_pod_info` | Pod identity | `pod`, `node`, `pod_ip`, `host_ip` | 2 series for platform-lab |
| `kube_node_info` | Node identity | `node`, `internal_ip`, `kubelet_version` | 3 nodes |

**What this tells an SRE:** desired vs available replicas and HPA intent — without looking at `kubectl get` every time, and with **history** in Prometheus.

**What this does not tell an SRE:** whether a pod is CPU-throttled right now (that is Metrics Server / cAdvisor territory).

---

## 6. Metrics Server

| Item | Value |
|---|---|
| Namespace | `kube-system` |
| Deployment | `metrics-server` 1/1 |
| Image | `registry.k8s.io/metrics-server/metrics-server:v0.9.0` |
| API | Metrics API (used by `kubectl top` and HPA resource metrics) |

### Live `kubectl top` (from Metrics Server)

| Node | CPU | Memory |
|---|---|---|
| k8s-ctrl-01 | 122m (3%) | 3657Mi (46%) |
| k8s-worker-01 | 62m (1%) | 1623Mi (27%) |
| k8s-worker-02 | 47m (1%) | 2799Mi (48%) |

| Pod | CPU | Memory |
|---|---|---|
| platform-lab pods | ~2m each | ~40Mi each |

### Conceptual difference

| | Metrics Server | Prometheus |
|---|---|---|
| Purpose | Near-real-time resource usage for **autoscaling / top** | Time-series store for **history, PromQL, Grafana** |
| Retention | Short window | Hours/days (lab: kube-prometheus-stack PVC retention) |
| HPA in this project | **Yes — drives HPA** | **No — does not drive HPA** |
| Scraped by Prometheus? | Not in this architecture | N/A |

---

## 7. Prometheus

| Item | Value |
|---|---|
| Version | **3.14.0** |
| UI/API | ClusterIP `kube-prometheus-stack-prometheus:9090` (port-forward for local access) |
| Active targets | **28** |

### Target jobs (live)

| Job | Count | Health | Maps to |
|---|---|---|---|
| `platform-lab` | 2 | UP | Application `/metrics` |
| `kube-state-metrics` | 1 | UP | KSM |
| `node-exporter` | 3 | UP | DaemonSet exporters |
| `kube-prometheus-stack-prometheus` | 2 | UP | Prometheus self (+ reloader) |
| `kubelet` | 9 | UP | Stack defaults |
| `coredns` | 2 | UP | Stack defaults |
| `apiserver` | 1 | UP | Stack defaults |
| `kube-prometheus-stack-grafana` / `operator` | 1 each | UP | Stack components |
| `kube-controller-manager` / `kube-scheduler` / `kube-etcd` / `kube-proxy` | several | **DOWN** | Common lab noise (control-plane insecure ports / kube-proxy metrics not exposed) |

DOWN targets here are **not** application failures. Prefer focusing on `platform-lab`, `kube-state-metrics`, and `node-exporter` for platform health.

### Data path

```text
source endpoint
  → ServiceMonitor selector
  → Prometheus Operator
  → scrape config
  → Prometheus TSDB
  → PromQL API
  → Grafana datasource "prometheus"
```

---

## 8. Grafana

| Item | Value |
|---|---|
| Version | **13.2.2** |
| URL | http://192.168.56.201 |
| Platform/SRE dashboard | **Kubernetes Platform VMware** · UID `kubernetes-platform-vmware` |
| App dashboard | existing `platform-lab` dashboard (kept separate) |
| Provisioning | ConfigMaps labeled `grafana_dashboard=1` via GitOps |

### Five real panels and their sources

| Panel title | PromQL | Metric source | What it tells you |
|---|---|---|---|
| Nodes UP | `count(up{job="node-exporter"} == 1)` | node-exporter targets | Are all 3 nodes exporting? |
| Cluster memory util | `1 - (sum(MemAvailable) / sum(MemTotal))` | node-exporter | Cluster memory pressure at a glance |
| Available replicas | `kube_deployment_status_replicas_available{namespace="$namespace",deployment="$deployment"}` | kube-state-metrics | Is the Deployment actually available? |
| HTTP request rate | `sum(rate(http_requests_total{job="platform-lab",namespace="$namespace"}[5m]))` | application | Traffic trend |
| KSM target | `max(up{job="kube-state-metrics"})` | Prometheus scrape health | Is Kubernetes-state telemetry flowing? |

Path for every panel:

```text
Metric source → Prometheus scrape → PromQL in panel → Grafana visualization
```

---

## 9. End-to-End Data Flow

```text
                    ┌──────────────────────┐
                    │   Kubernetes API     │
                    └──────────┬───────────┘
                               │ watch
                               ▼
                    ┌──────────────────────┐
                    │ kube-state-metrics   │
                    └──────────┬───────────┘
                               │ :8080/metrics
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
 ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
 │ platform-lab    │  │ node-exporter   │  │ (other SM jobs) │
 │ :8000/metrics   │  │ :9100/metrics   │  │                 │
 └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
          │                    │                    │
          └────────────┬───────┴────────────────────┘
                       ▼
              ┌─────────────────┐
              │   Prometheus    │
              │   (TSDB)        │
              └────────┬────────┘
                       │ PromQL
                       ▼
              ┌─────────────────┐
              │     Grafana     │
              └─────────────────┘

Separately (autoscaling path — NOT Prometheus):

  kubelet → Metrics Server → Metrics API → HPA → Deployment replicas
```

---

## 10. Metric Examples

### A. Application — `http_requests_total`

| Role | Component |
|---|---|
| PRODUCES | FastAPI / Prometheus client in platform-lab |
| SCRAPES | Prometheus (ServiceMonitor `platform-lab`) |
| STORES | Prometheus TSDB |
| QUERIES | PromQL `rate(...[1m])` |
| VISUALIZES | Grafana “HTTP request rate” |

### B. Node — `node_memory_MemAvailable_bytes`

| Role | Component |
|---|---|
| PRODUCES | Linux node via node-exporter |
| SCRAPES | Prometheus (ServiceMonitor node-exporter) |
| STORES | Prometheus TSDB |
| QUERIES | PromQL with MemTotal for utilization |
| VISUALIZES | Grafana “Node memory utilization” |

### C. Kubernetes state — `kube_deployment_status_replicas_available`

| Role | Component |
|---|---|
| PRODUCES | kube-state-metrics from API object status |
| SCRAPES | Prometheus (ServiceMonitor kube-state-metrics) |
| STORES | Prometheus TSDB |
| QUERIES | PromQL filter `namespace/deployment` |
| VISUALIZES | Grafana “Available replicas” / desired-vs-available |

---

## 11. PromQL Examples

Executed live against VMware Prometheus (results approximate; rerun for current values).

| Query | Transformation | Live result | Why SRE cares |
|---|---|---|---|
| `sum(rate(http_requests_total{job="platform-lab"}[1m]))` | counter → req/s | ~0.33 | Traffic / saturation signal |
| `1 - avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))` | idle counter → util | ~2–5% per node | Node CPU pressure |
| `1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)` | gauges → util | ~23–37% | Node memory pressure |
| `kube_deployment_status_replicas_available{namespace="platform-lab",deployment="platform-lab"}` | raw gauge | **2** | App availability |
| `kube_horizontalpodautoscaler_status_current_replicas{namespace="platform-lab"}` | raw gauge | **2** | Current scale |
| `kube_horizontalpodautoscaler_status_desired_replicas{namespace="platform-lab"}` | raw gauge | **2** | Desired scale (compare to current) |

---

## 12. Metrics Server vs Prometheus

```text
Metrics Server  →  short-term CPU/memory  →  HPA / kubectl top
Prometheus      →  historical multi-source metrics  →  Grafana / investigation
```

Rules of this lab:

1. **HPA broken?** Start with Metrics Server + `kubectl top` + HPA object — not Grafana.
2. **Dashboard empty / odd history?** Start with Prometheus targets + PromQL — not Metrics Server.
3. **Replica count wrong on a chart?** Check kube-state-metrics — not Metrics Server.

---

## 13. Exporter vs Collector vs Visualization

| Term | In this lab | Example |
|---|---|---|
| **Exporter** | Process that exposes `/metrics` about something else | node-exporter, kube-state-metrics |
| **Instrumented app** | App exposes its own `/metrics` | platform-lab |
| **Collector / scraper** | Periodically pulls `/metrics` | Prometheus |
| **Store** | Time-series database | Prometheus TSDB |
| **Visualization** | Charts / stats over PromQL | Grafana |
| **Resource metrics API** | Separate path for HPA | Metrics Server |

---

## 14. Troubleshooting Flow

### Empty Grafana panel

```text
Grafana panel empty / No data
    ↓
Confirm PromQL in Explore against datasource "prometheus"
    ↓
Check Prometheus Targets UI / API: is the job UP?
    ↓
Check exporter or app /metrics directly (port-forward)
    ↓
Check Service + Endpoints (do backends exist?)
    ↓
Check Pod Ready / logs (still read-only first)
```

### node-exporter missing a node

```text
Expected 3 node-exporter targets, see fewer
    ↓
kubectl get ds -n monitoring ...node-exporter
    ↓
kubectl get pods -o wide -n monitoring -l app.kubernetes.io/name=prometheus-node-exporter
    ↓
Is the node Ready? Is the DaemonSet pod Pending/CrashLoop?
    ↓
Check Prometheus ServiceMonitor / endpoints for that Service
```

### kube-state-metrics missing deployment series

```text
Expected kube_deployment_* for platform-lab missing
    ↓
up{job="kube-state-metrics"} == 1 ?
    ↓
curl KSM /metrics | grep kube_deployment_spec_replicas
    ↓
Does the Deployment exist in API? (kubectl get deploy -n platform-lab)
    ↓
RBAC / collector list (configuration — do not change in this lab)
```

### HPA not scaling (separate path!)

```text
HPA not scaling
    ↓
kubectl get hpa -n platform-lab
    ↓
kubectl describe hpa -n platform-lab   # "failed to get cpu" ?
    ↓
Metrics Server pod healthy?
    ↓
kubectl top pods -n platform-lab
    ↓
Do pods have resources.requests.cpu set?
    ↓
HPA min/max / target utilization configuration
```

Remember: fixing Prometheus will **not** fix HPA if Metrics Server is broken.

---

## Appendix — Inspection commands used (read-only)

```powershell
kubectl --context=ckad-lab get nodes -o wide
kubectl --context=ckad-lab get deploy,ds,svc -A
kubectl --context=ckad-lab get servicemonitor -A
kubectl --context=ckad-lab top nodes
kubectl --context=ckad-lab top pods -n platform-lab

# Temporary local viewers only (no config changes):
kubectl --context=ckad-lab -n platform-lab port-forward svc/platform-lab 18000:8000
kubectl --context=ckad-lab -n monitoring port-forward svc/kube-prometheus-stack-kube-state-metrics 18080:8080
kubectl --context=ckad-lab -n monitoring port-forward svc/kube-prometheus-stack-prometheus 19090:9090
```

Grafana: open http://192.168.56.201 → dashboard **Kubernetes Platform VMware**.
