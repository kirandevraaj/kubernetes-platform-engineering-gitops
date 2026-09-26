# Golden signals (mapped to Project 1)

Google SRE framing: **Latency, Traffic, Errors, Saturation** (+ **Availability** for operators).

Do **not** invent app latency SLOs — map only what the lab exposes.

---

## Signal matrix

| Signal | What it means | Project 1 source | How to check (READ-ONLY) |
|---|---|---|---|
| **Availability** | Can users reach `/health`? | Ingress VIP / ALB | VMware: curl VIP; AWS: ALB target health |
| **Latency** | Response time | App may expose metrics | Prometheus histogram **if** scraped — **Not verified** as SLO |
| **Traffic** | Request rate | `/metrics` or ingress logs | Generate test traffic in lab |
| **Errors** | 5xx rate | Ingress / ALB / app logs | curl codes; Grafana panels if configured |
| **Saturation** | CPU/memory/pod density | HPA, node allocatable | `kubectl top`; HPA status; **Observed** 17-pod/node pressure on t3.medium |

---

## Kubernetes platform signals

| Object | Healthy signal | Unhealthy signal |
|---|---|---|
| Pod | `Ready=True` | NotReady, CrashLoop |
| Deployment | `availableReplicas == spec.replicas` | Progressing stuck |
| Node | `Ready` | NotReady, pressure |
| PVC | `Bound` | `Pending` |
| Argo Application | `Synced` + `Healthy` | Degraded, ComparisonError |
| Prometheus target | UP | DOWN for app ServiceMonitor |
| Metrics Server | `kubectl top nodes` works | APIService unavailable |

---

## Application — `platform-lab`

| Signal | Detail |
|---|---|
| Version | Tag `0.1.4`, digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |
| Probe path | `/health` (**Observed** 200 when healthy) |
| Metrics | `/metrics` on port 8000 — scrape via ServiceMonitor |
| HPA | **Observed** scale-up VMware 2→4, AWS 2→3 under load |

---

## Ingress / load balancing

| Env | Signal |
|---|---|
| VMware | MetalLB VIP `192.168.56.200`; ingress-nginx 2 replicas |
| AWS | ALB listener + target group healthy; target type **ip** |

---

## Storage

| Env | Signal |
|---|---|
| VMware | PVC Bound to local-path |
| AWS | PVC Bound; EBS `in-use`; VolumeAttachment attached |

---

## GitOps

| Signal | Meaning |
|---|---|
| `sync.status` Synced | Cluster matches Git |
| OutOfSync | Drift or pending change |
| selfHeal | **Observed** ~6s correction on VMware drift test |

---

## Related

- [daily-platform-health.md](../checklists/daily-platform-health.md)
- [architecture/observability.md](../architecture/observability.md)
- [troubleshooting-matrix.md](../troubleshooting/troubleshooting-matrix.md)
