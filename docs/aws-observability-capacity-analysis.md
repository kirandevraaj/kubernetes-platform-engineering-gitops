# AWS EKS Observability Capacity Analysis

**Date:** 2026-09-25  
**Cluster:** `platform-lab-aws-lab-eks` (`ap-south-1`, Kubernetes **1.36**, status **ACTIVE**)  
**Git baseline at analysis:** `5da676ff213b706ae9a51ce2728b68d946e5b71c`  
**Nature of this document:** read-only capacity and compatibility assessment. **Nothing was deployed.**

---

## 1. Environment

| Item | Measured value |
|---|---|
| kubectl context | `platform-lab-aws` |
| API endpoint region marker | `*.gr7.ap-south-1.eks.amazonaws.com` (EKS, not VMware) |
| Node group | **2 × t3.small** (private nodes; no EXTERNAL-IP) |
| Zones | `ap-south-1a`, `ap-south-1b` |
| Node kubelet | `v1.36.4-eks-f4fc4f1` |
| Application | `platform-lab` **2/2** Ready, image digest-pinned, HPA **min 2 / max 4** (idle CPU ~6% of request) |
| Platform components present | Argo CD, AWS Load Balancer Controller, Metrics Server |
| Observability stack on AWS | **Not installed** (confirmed absent — see §6) |

This analysis deliberately targets the **AWS EKS** cluster, not the VMware kubeadm lab.

---

## 2. Current Cluster Capacity

Values below are from `kubectl get nodes -o json`, `kubectl describe nodes`, and `kubectl top nodes` (Metrics Server).

### Per node (identical capacity class)

| Metric | Node A `ip-10-50-41-249…` | Node B `ip-10-50-55-175…` |
|---|---|---|
| Instance type | t3.small | t3.small |
| CPU capacity | 2 cores | 2 cores |
| CPU allocatable | **1930m** | **1930m** |
| Memory capacity | **1955572Ki (~1910 Mi)** | **1955572Ki (~1910 Mi)** |
| Memory allocatable | **1468148Ki (~1434 Mi)** | **1468148Ki (~1434 Mi)** |
| Pod capacity / allocatable | **11** | **11** |
| Allocated CPU requests (describe) | 300m (15%) | 400m (20%) |
| Allocated memory requests (describe) | 264Mi (18%) | 204Mi (14%) |
| Allocated CPU limits (describe) | 200m (10%) | 200m (10%) |
| Allocated memory limits (describe) | 128Mi (8%) | 468Mi (32%) |
| Actual CPU usage (`kubectl top`) | **44–111m (~2–5%)** | **29–43m (~1–2%)** |
| Actual memory usage (`kubectl top`) | **~995–996 Mi (~69%)** | **~833 Mi (~58%)** |

### Cluster totals

| Metric | Value |
|---|---|
| Total CPU capacity | **4.0** cores |
| Total CPU allocatable | **3.86** cores (3860m) |
| Total memory capacity | **~3819 Mi** |
| Total memory allocatable | **~2867 Mi** |
| Total pod slots (allocatable) | **22** |
| Running non-terminal pods | **18** |
| Approximate unused pod slots | **4** |
| Sum of CPU requests (all pods) | **700m (18.1% of allocatable)** |
| Sum of memory requests (all pods) | **468 Mi (16.3% of allocatable)** |
| Sum of CPU limits | **400m** |
| Sum of memory limits | **596 Mi** |
| Actual CPU usage (sum of nodes) | **~73m (≈1.9% of allocatable)** |
| Actual memory usage (sum of nodes) | **~1829 Mi (≈63.8% of allocatable)** |
| Remaining schedulable CPU (by requests) | **~3.16 cores** |
| Remaining schedulable memory (by requests) | **~2400 Mi** |
| Remaining memory vs **actual** usage | **~2867 − 1829 ≈ 1038 Mi** before allocatable exhaustion |

**Primary binding constraints (measured):**

1. **Pod density** — only **~4** free pod slots cluster-wide on t3.small ENI limits.  
2. **Actual memory usage** — already **~64%** of allocatable despite low requests (BestEffort / unset-request workloads).  
3. CPU is **not** the binding constraint today.

---

## 3. Current Resource Consumption

### Node-level picture

CPU is nearly idle. Memory is the scarce runtime resource:

- Node A ≈ **69%** memory used with only **15%** CPU requested.  
- Node B ≈ **58%** memory used.

That gap exists because several important workloads set **no requests** (Argo CD, AWS Load Balancer Controller) yet still consume tens to hundreds of MiB of RSS.

### Application HPA interaction

| Field | Measured |
|---|---|
| HPA target | CPU 70% of request |
| Current | **6% (3m)** / 70% |
| Replicas | **2** (min); max **4** |
| Per-replica requests | **50m CPU / 64Mi memory** |
| Per-replica limits | **200m CPU / 128Mi memory** |
| Actual usage per app pod | **~3m CPU / ~40Mi memory** |

At idle, the app is a light consumer. If HPA reaches **4** replicas, expect **+100m CPU / +128Mi memory requests** and **+2 pods** — cutting free pod slots from **~4 → ~2**.

---

## 4. Existing System Workloads

Grouped from live pods + container resource specs + `kubectl top`.

| Group | Pods | CPU req (sum) | Mem req (sum) | CPU lim (sum) | Mem lim (sum) | Approx actual CPU | Approx actual mem |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. EKS/system** (aws-node, kube-proxy, CoreDNS, pod-identity) | 8 | 500m | 140 Mi | 0 (mostly unset) / CoreDNS mem lim 170Mi×2 | ~340 Mi lim on CoreDNS path | ~12m | ~188 Mi |
| **B. Argo CD** | 5 | **0** (unset) | **0** | **0** | **0** | ~7m | **~198 Mi** (controller alone ~108 Mi) |
| **C. AWS Load Balancer Controller** | 2 | **0** | **0** | **0** | **0** | ~4m | ~59 Mi |
| **D. Metrics Server** | 1 | 100m | 200 Mi | unset | unset | ~3m | ~20 Mi |
| **E. platform-lab** | 2 | 100m | 128 Mi | 400m | 256 Mi | ~6m | ~80 Mi |
| **F. other** | 0 | — | — | — | — | — | — |

### DaemonSets (per-node tax)

| DaemonSet | Ready | Notes |
|---|---|---|
| `aws-node` (VPC CNI) | 2/2 | ~56–58 Mi each (measured) |
| `kube-proxy` | 2/2 | ~14–18 Mi each |
| `eks-pod-identity-agent` | 2/2 | ~10 Mi each |

Three DaemonSets already occupy **3 of 11** pod slots per node before any app or observability DaemonSet.

### Notable scheduling quirk

Argo CD and the Load Balancer Controller contribute **real memory** but **zero requests**, so `kubectl describe` “Allocated resources” understates pressure relative to `kubectl top`. Any observability design that only looks at request headroom will overestimate safety.

---

## 5. Current Scheduling Headroom

| Question | Answer from measurements |
|---|---|
| Remaining schedulable CPU (requests) | **~3160m** — ample |
| Remaining schedulable memory (requests) | **~2400 Mi** — looks ample **on paper** |
| Remaining memory vs actual usage | **~1.0 Gi** cluster-wide before allocatable saturation |
| Unused pod slots | **~4** |
| ResourceQuota / LimitRange | **None** |
| PVCs / PVs | **None** |
| StorageClass | **`gp2`** (`kubernetes.io/aws-ebs`, `WaitForFirstConsumer`, expansion **false**) |
| Node near pod-count limit? | **Yes — Node A hosts ~10/11 pods**; cluster only has **4** free slots |
| High limits causing schedule friction? | App limits are modest. CoreDNS has memory limits. Bigger issue is **missing requests** on Argo/LBC (overscheduling risk), not huge limits |

**Implication:** observability additions must be sized first against **pod slots** and **actual memory**, not against the optimistic request remainder.

---

## 6. Observability Components Considered

### Actually installed today

| Component | Status |
|---|---|
| Metrics Server | **Installed** (`kube-system/metrics-server`, used by HPA / `kubectl top`) |
| Prometheus | **Absent** |
| Grafana | **Absent** |
| kube-state-metrics | **Absent** |
| node-exporter / node-problem detectors | **Absent** |
| Alertmanager | **Absent** |
| OpenTelemetry Collector / Operator | **Absent** |
| Jaeger | **Absent** |
| kube-prometheus-stack / Prometheus Operator | **Absent** |

### CRDs

`kubectl get crd` filtered for prometheus/grafana/monitor/otel/jaeger/alertmanager: **no matches**.  
Total CRDs in cluster: **14** (platform / Argo / AWS LB related — not observability).

### Namespaces / Services / Pods

Namespaces: `argocd`, `default`, `kube-*`, `platform-lab` only.  
No Services or Pods matching prometheus/grafana/alertmanager/otel/jaeger/kube-state/node-exporter/thanos.

---

## 7. Capacity Scenarios

Suggested requests are **lab planning figures**, not measured post-deploy values. They follow common lightweight chart defaults scaled down for t3.small.

### Component planning table

| Component | Replicas | Minimal CPU req | Minimal mem req | Conservative CPU req | Conservative mem req | Why |
|---|---:|---|---|---|---|---|
| Prometheus | 1 | 100m | 256Mi | 200m | 512Mi | TSDB + scrape; memory grows with series/retention |
| Grafana | 1 | 50m | 128Mi | 100m | 256Mi | UI + SQLite; dashboards add RSS |
| kube-state-metrics | 1 | 50m | 64Mi | 100m | 128Mi | API watch; modest on small clusters |
| node-exporter | 2 (DS) | 50m×2 | 32Mi×2 | 100m×2 | 64Mi×2 | One pod **per node**; costs **2 pod slots** |
| Alertmanager | 1 | 50m | 64Mi | 100m | 128Mi | Mostly idle in a lab without real paging |
| OpenTelemetry Collector | 1 | 100m | 128Mi | 200m | 256Mi | Pipeline buffers; overlaps Prometheus for metrics |

### Aggregate request models

| Scenario | Components | Pods added | Minimal Σ CPU / mem | Conservative Σ CPU / mem | Fits in **4** free pod slots? | Fits in **~1.0 Gi** actual mem headroom? |
|---|---|---:|---|---|---|---|
| **A** | Prometheus + Grafana | 2 | 150m / 384Mi | 300m / 768Mi | **Yes** | **Likely** if RSS stays near requests; tight if Prom grows |
| **B** | A + kube-state-metrics + node-exporter | **5** | 300m / 512Mi | 600m / 1024Mi | **No (needs 5; have ~4)** | Conservative mem ≈ entire free actual headroom |
| **C** | B + Alertmanager | **6** | 350m / 576Mi | 700m / 1152Mi | **No** | **Risky / no** under conservative |
| **D** | B + OTel Collector (no Alertmanager) | **6** | 400m / 640Mi | 800m / 1280Mi | **No** | **No** under conservative |

**CPU:** all scenarios are fine against measured request and usage headroom.  
**Pod slots:** Scenario A is the only scenario that clearly fits today; B/C/D fail the measured **4-slot** ceiling unless something else is removed or nodes are enlarged.  
**Memory:** Scenario A conservative (768Mi requests) is schedulable by requests and plausible against ~1038Mi actual free **only if** Prometheus RSS stays controlled (short retention, few targets).

---

## 8. Prometheus Storage Considerations

### Measured storage facts

- StorageClass **`gp2`** is available.  
- **Zero** PVCs/PVs exist today.  
- Nodes have ~20 Gi ephemeral disks; allocatable ephemeral-storage ≈ 18 Gi each (from node status).

### Lab sizing assumptions (not measurements)

| Assumption | Suggested lab default | Rationale |
|---|---|---|
| Retention | **6–24 hours** (not 15d) | Small node memory + disk; lab traffic is low |
| Scrape interval | **30–60s** | Reduces series churn vs 15s defaults |
| Targets | app ServiceMonitor + limited kubelet/cAdvisor if enabled; avoid scraping everything | Fewer series → less RAM |
| PVC size if using EBS | **5–10 Gi gp2** | Enough for short retention on a tiny app; expand later if needed |
| emptyDir alternative | Possible for throwaway lab | Data lost on reschedule; avoids PVC but still consumes node ephemeral + memory-mapped TSDB pressure |

**Risk:** Prometheus memory is dominated by **active series**, not by the PVC size. A tiny PVC with aggressive scraping can still OOM a t3.small node.

**Recommendation if deployed later:** single Prometheus replica, short retention, explicit memory request **and** limit, prefer a small **gp2 PVC** over unbounded emptyDir growth for crash diagnostics — but accept that persistence is optional for this lab.

---

## 9. Grafana Considerations

| Topic | Assessment against measurements |
|---|---|
| Single replica fit | **Yes** under Scenario A (1 extra pod, ~128–256Mi request) |
| Memory overhead | Modest vs Prometheus; measured cluster can absorb one Grafana if Prom is controlled |
| Dashboard complexity | Keep **few** dashboards; avoid heavy forever-refresh panels on a small Prom |
| SQLite vs external DB | **SQLite (default)** is appropriate for this lab; external DB would add another workload the cluster cannot spare |
| Persistence | Optional PVC for Grafana data; not required for a disposable lab |
| Impact on 2×t3.small | Acceptable as part of Scenario A; not acceptable if stacked with DaemonSet exporters without more slots |

---

## 10. Operational Risks

| Risk | Evidence from this cluster | Severity for observability add-on |
|---|---|---|
| **Memory pressure / eviction** | Nodes already **58–69%** mem used; ~1 Gi free actual | **High** if Prometheus retention/scrape is not capped |
| **Pod-slot exhaustion** | **18/22** pods; Node A ~10/11 | **High** for any DaemonSet exporter |
| CPU contention | Usage ~2% allocatable | **Low** today |
| DaemonSet overhead | 3 DS already; node-exporter adds +1/node | **High** for Scenario B+ |
| Prometheus memory growth | Not installed; known failure mode on small nodes | **High** (assumptive, but material) |
| Storage consumption | gp2 available; no PVC yet | **Medium** — manageable with 5–10 Gi + short retention |
| HPA interaction | Max scale adds **+2 pods** and +128Mi requests | **Medium** — reduces free slots to ~2 |
| Missing requests on Argo/LBC | Real RSS without scheduler accounting | **Medium** — scheduler may pack observability onto a hot node |
| Noisy neighbor | App is tiny; Argo controller is top mem consumer (~108Mi) | **Medium** |
| Loss of monitoring under pressure | If Prom shares the only stressed node | **Medium** — prefer anti-affinity / avoid colocating Prom+Grafana on the fullest node when deploying later |

---

## 11. Recommended Lab Architecture

### Smallest sensible architecture for *this* measured cluster

**Deploy later (not now):**

1. **Prometheus** (1) — short retention, slow scrape, memory request+limit  
2. **Grafana** (1) — SQLite, ClusterIP or internal ALB path, few dashboards  
3. Optionally **kube-state-metrics** (1) **only if** pod-slot count is re-checked and still ≥1 free after Prom+Grafana schedule, **and** HPA is not at max

**Defer on capacity grounds:**

| Component | Why defer (measurement-linked) |
|---|---|
| **node-exporter DaemonSet** | Needs **2** pods; cluster has only **~4** free slots and HPA may consume 2; Node A is already near the **11-pod** ENI ceiling |
| **Alertmanager** | Extra pod + memory for little lab value without a paging workflow; worsens slot pressure |
| **OpenTelemetry Collector** | Extra pod + buffers; overlaps Prometheus for metrics; no traces stack to feed yet |
| Full **kube-prometheus-stack** defaults | Chart defaults (multiple exporters, longer retention, operator) exceed measured slot/memory comfort on 2×t3.small |

### Cost-conscious posture

Stay on **2×t3.small**. Do **not** resize nodes solely for a “complete” observability suite. Prefer a **minimal Prom+Grafana** pair that answers “is my app healthy?” over a production-grade metrics platform.

---

## 12. Pre-Deployment Gates

Before any future install (separate milestone), re-verify **read-only**:

1. `kubectl top nodes` — memory **< ~70%** on both nodes (or accept higher risk explicitly).  
2. Free pod slots: `allocatable pods − running pods ≥ 3` (Prom+Grafana+buffer), ideally **≥ 4** if adding kube-state-metrics.  
3. HPA replicas still **2** (or account for max=4 in the slot budget).  
4. Confirm still **no** competing observability install.  
5. Choose Prometheus retention ≤ **24h** and memory **limit** ≤ **512Mi** unless nodes are enlarged.  
6. Prefer scheduling Prometheus onto the **less memory-full** node if practical.  
7. Create at most one small **gp2** PVC (e.g. 5–10 Gi) — do not enable volume expansion expectations (`allowVolumeExpansion: false` on gp2 today).  
8. Do **not** install node-exporter until nodes are larger **or** pod limit increases (instance type / prefix delegation changes — out of scope here).

---

## 13. Measurements Used

Collected **2026-09-25** via read-only commands against context `platform-lab-aws`:

- `kubectl config current-context`, `kubectl cluster-info`  
- `aws eks describe-cluster --name platform-lab-aws-lab-eks --region ap-south-1`  
- `kubectl get nodes -o wide`, `kubectl get nodes -o json`, `kubectl describe nodes`, `kubectl top nodes`  
- `kubectl top pods -A`, `kubectl get pods -A -o wide`, `kubectl get pods -A -o json`  
- `kubectl get deploy,sts,ds -A`, `kubectl get daemonsets -A`  
- `kubectl get resourcequota -A`, `kubectl get limitrange -A`  
- `kubectl get pvc -A`, `kubectl get pv`, `kubectl get storageclass`  
- `kubectl get ns`, `kubectl get crd`, `kubectl get svc -A`  
- `kubectl get hpa -A`, `kubectl describe hpa -n platform-lab`  
- `kubectl get deploy -A -o json` (requests/limits)

No `terraform apply/destroy`, Helm install/upgrade, or mutating kubectl verbs were used.

---

## 14. Conclusion

| Question | Explicit answer |
|---|---|
| Measured CPU headroom | **~3.16 cores** free by requests; **~98%** unused by actual usage (~73m used of 3860m allocatable) |
| Measured memory headroom | **~2400 Mi** free by requests, but only **~1038 Mi** free vs **actual** usage; nodes already **58–69%** mem utilized |
| Measured pod-slot headroom | **~4** free slots cluster-wide; one node near **11/11** density |
| Feasible on this cluster (lab) | **Prometheus + Grafana** (Scenario A), tightly configured |
| Conditionally feasible | **kube-state-metrics** only after re-counting free slots post Prom/Grafana and with HPA still at 2 |
| Risky / defer | **node-exporter**, **Alertmanager**, **OpenTelemetry Collector**, default **kube-prometheus-stack** footprint |
| Key assumptions | Suggested component request sizes; Prometheus RSS stays near request under short retention; no unexpected DaemonSets added; HPA not scaled to 4 during install |
| Re-measure after any future deploy | `kubectl top nodes/pods`, pod count vs 22, Prometheus RSS vs limit, PVC usage, HPA replica count |
| Do **not** deploy on this cluster | Full multi-exporter observability suite; long Prometheus retention; OTel+Alertmanager+node-exporter together; anything requiring **>4** extra pods without node capacity changes |

**Bottom line:** This **2×t3.small** EKS lab has abundant **CPU** but constrained **memory reality** and severe **pod-density** limits. A **minimal Prometheus + Grafana** lab stack is the only clearly compatible observability footprint today. Everything else should wait for more node capacity or a deliberate trade (removing/relocating workloads) — and **must not** be installed as part of this analysis milestone.
