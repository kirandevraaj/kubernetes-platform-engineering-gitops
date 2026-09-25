# AWS HPA + Observability Load Test

**Date:** 2026-09-25 (UTC)  
**Cluster:** `platform-lab-aws-lab-eks` (`platform-lab-aws`)  
**Application version:** `0.1.4`  
**Image digest:** `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## 1. Objective

Validate, under **controlled** in-cluster HTTP load, that:

1. Application traffic increases CPU utilization observed by **Metrics Server**
2. The existing **HPA** scales `platform-lab` upward when CPU exceeds its configured target
3. **Prometheus** continues scraping `/metrics` from all application pods (including newly created ones)
4. **Grafana** can visualize application request/process metrics during the event
5. After load stops, CPU returns toward baseline and HPA scales back down per its live configuration

This was a temporary experiment. No permanent load-testing workload remains.

## 2. Architecture

```text
                 HTTP load (temporary Job)
                          ↓
                    platform-lab
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
      Metrics Server                 /metrics
            │                           │
            ▼                           ▼
           HPA                      Prometheus
            │                           │
            ▼                           ▼
     Replica scaling                  Grafana
```

**Explicit separation:**

| Path | Purpose |
|---|---|
| **Metrics Server → HPA** | Resource metrics (CPU % of request) drive replica count |
| **Prometheus → Grafana** | Application `/metrics` for dashboards |

**Prometheus is not the HPA metrics provider.**

## 3. Baseline

| Item | Measured value |
|---|---|
| Context | `platform-lab-aws` |
| Initial replicas | **2** |
| HPA `minReplicas` | **2** |
| HPA `maxReplicas` | **4** |
| HPA CPU target | **70%** of request |
| HPA current CPU | **6% (3m)** |
| App pod CPU / mem | ~2–3m / ~40Mi each |
| Node usage | ~53–57m + ~24–34m CPU; ~1400Mi (~42%) + ~450Mi (~13%) mem |
| Observability | Prometheus ~5m/35Mi; Grafana ~5m/152Mi |
| Image | digest-pinned `0.1.4` artifact above |

## 4. Load Generator

| Field | Value |
|---|---|
| Kind | Temporary Kubernetes **Job** (not GitOps) |
| Name | `platform-lab-hpa-load-tmp` |
| Namespace | `platform-lab` |
| Image | **`curlimages/curl:8.11.1`** (pinned; not `:latest`) |
| Target | `http://platform-lab.platform-lab.svc.cluster.local:8000` (`/health` + `/metrics`) |
| Concurrency | stepped **30 → 80 → 120** (planned); scale-up occurred during early phase |
| Duration bound | `activeDeadlineSeconds: 420`; script deleted Job after observation |
| Resources | requests `50m/32Mi`, limits `250m/64Mi` |
| Labels | `platform-lab.io/temporary=true` |

**Temporary nature:** applied with `kubectl` for the experiment only, then deleted. **Not** committed to GitOps.

**Note:** the load Job later hit **OOMKilled** on its own 64Mi limit under high concurrency. That truncated load early but **after** HPA had already scaled. Application pods were not OOMKilled.

## 5. Scaling Event

| Milestone (UTC) | Observation |
|---|---|
| `08:42:51` **T0** | Baseline: 2 replicas, CPU 6% |
| `08:42:55` **T1** | Load Job applied |
| `08:43:34` | HPA CPU **49% (24m)** — rising, still below scale decision |
| `08:43:55`–`08:44:00` **T2/T3** | HPA CPU **90–97% (45–48m)**; **desired replicas → 3** |
| `08:44:00` | **Scale-up detected** (2 → 3) |
| `08:44:01`–`08:44:16` **T4** | New pod `…-b5gz7` Running → **Ready** (~37s after creation) |
| `08:44:38` | Load Job **OOMKilled** (generator limit); app CPU falls |
| `08:48:54` **T6** | Job deleted / confirmed gone |
| `08:49:59` **T8** | HPA **desired → 2** (scale-down) |
| `08:50:20` | Settled at **2** replicas, CPU **6%** |

| Metric | Value |
|---|---|
| Peak HPA CPU | **90%** (poll peak; **97%** seen one sample earlier) |
| Peak replicas | **3** (did not reach max 4) |
| Time to first scale-up | **~65 seconds** after load apply |
| Time for new pod Ready | **~37 seconds** after pod creation (~1s after desired=3 observed ReadyReplicas=3 in script timing) |

HPA settings were **not** modified.

## 6. Prometheus Observations

### Actual metric names used (verified from `/metrics`)

- `http_requests_total`
- `http_request_duration_seconds` (and related)
- `process_cpu_seconds_total`
- `process_resident_memory_bytes`
- `python_info` / GC metrics
- Prometheus `up`

### Useful PromQL

```promql
sum(rate(http_requests_total{job="platform-lab"}[1m]))
sum(rate(process_cpu_seconds_total{job="platform-lab"}[1m]))
up{job="platform-lab"}
```

### Targets during scale-out

All three application pods were **UP**, including the new replica:

- `platform-lab-7b897c78f8-9b755`
- `platform-lab-7b897c78f8-hvqg5`
- `platform-lab-7b897c78f8-b5gz7` (new)

Prometheus self-target remained **UP**.

## 7. Grafana Observations

Dashboard (Git-managed, unchanged for this experiment):

**`platform-lab AWS (lightweight)`** (`platform-lab-aws-lightweight`)

Panels used:

| Panel | Metric / query |
|---|---|
| Target up (platform-lab) | `min(up{job="platform-lab"})` |
| HTTP request rate | `sum(rate(http_requests_total{job="platform-lab"}[5m]))` |
| HTTP requests by handler | `sum by (handler) (rate(http_requests_total{job="platform-lab"}[5m]))` |
| Process resident memory | `process_resident_memory_bytes{job="platform-lab"}` |
| Process CPU seconds (rate) | `rate(process_cpu_seconds_total{job="platform-lab"}[5m])` |

**HPA replica count is not on the Grafana dashboard** — that would need kube-state-metrics (not installed). HPA state was captured with `kubectl get/describe hpa` during the run.

Access remains: `kubectl -n observability port-forward svc/grafana 3000:80`.

## 8. Recovery

| Item | Value |
|---|---|
| Effective load end | ~`08:44:38` (Job OOM) / Job deleted `08:48:54` |
| CPU after load | returned to **~6% (3m)** while still at 3 replicas |
| Scale-down time | **`08:49:59`** (~5–6 minutes after CPU returned to baseline — consistent with HPA scale-down stabilization) |
| Final replicas | **2** |
| Final CPU | **6% (3m)** |
| Final app memory | ~41Mi / pod |
| Final node memory | ~40% / ~16% |

## 9. Resource Impact

| Stage | App replicas | HPA CPU | Node mem (approx) | Notes |
|---|---:|---:|---|---|
| Before | 2 | 6% | 42% / 13% | Idle |
| During peak | 3 | 90–97% | 42% / 22% | Load Job ~250m CPU briefly |
| After | 2 | 6% | 40% / 16% | Settled |

Cluster was not exhausted. Highest node memory observed during the run stayed around the low-to-mid 40% range on the busier node.

## 10. Failure / Stress Guardrails

- Load targeted **ClusterIP Service**, not the public ALB
- Job `activeDeadlineSeconds: 420`
- Stepped concurrency instead of maximum blast
- Script aborted on node memory **> 85%** (not triggered)
- Load generator memory **limit 64Mi** (self-limited; OOM stopped generator, not the app)
- HPA **maxReplicas=4** as existing ceiling
- No HPA/Terraform/node changes
- Temporary Job deleted; no leftover Services/Ingress/ALB/PVC

## 11. Results

**Demonstrated successfully:**

- Metrics Server–driven HPA scale-up **2 → 3** when CPU exceeded 70% of request  
- New pod became Ready and was scraped by Prometheus (`up=1`)  
- Grafana dashboard metrics (`http_requests_total`, process metrics) remain the right panes for this path  
- After load ended, HPA scaled **3 → 2** without manual intervention  
- ALB `/health` = 200; `/version` = `0.1.4`; image digest unchanged  
- No application OOM/Evicted/MemoryPressure/CrashLoop  

**Caveat:** the temporary load Job OOMKilled itself; future experiments should raise generator memory slightly or reduce per-process concurrency, while keeping the generator disposable.

## 12. Lessons Learned

1. With a **50m CPU request**, HPA 70% is only **~35m** — modest concurrent HTTP load is enough to scale.
2. Keep **Metrics Server / HPA** and **Prometheus / Grafana** mentally and architecturally separate in docs and dashboards.
3. Bound temporary load Jobs with CPU/memory limits and deadlines; generator OOM is preferable to node pressure.
4. Expect **multi-minute** HPA scale-down lag even after CPU returns to idle.
5. Prometheus endpoint discovery automatically picked up the new pod — no scrape config change was required.

## 13. Next Steps

Analysis only — **not implemented** in this milestone:

| Idea | Why later |
|---|---|
| kube-state-metrics | Grafana panels for HPA/Deployment replica counts |
| node-exporter | Node-level CPU/mem dashboards |
| Alertmanager | Alert on sustained high latency / error rate |
| OpenTelemetry | Traces once an app instrumentation path exists |
| Richer k8s dashboards | Depend on the above exporters |

Re-measure capacity before adding DaemonSets or multi-exporter stacks.
