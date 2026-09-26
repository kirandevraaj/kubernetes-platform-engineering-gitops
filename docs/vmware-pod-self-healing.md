# VMware Kubernetes Pod Failure and Self-Healing

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Experiment type:** Controlled single-pod deletion  
**AWS:** not modified  

---

## 1. Objective

Prove Kubernetes **native self-healing** for the `platform-lab` Deployment by deleting **exactly one** application pod and observing:

Deployment → ReplicaSet → replacement Pod → Ready → Service endpoints → Prometheus scrape recovery

without changing Deployment, HPA, PDB, probes, networking, or GitOps manifests.

---

## 2. Initial Architecture

```text
Ingress (ingress-nginx / MetalLB VIP 192.168.56.200)
  Host: platform-lab.local
        │
        ▼
Service/platform-lab (ClusterIP :8000)
        │
        ├─ Pod A
        └─ Pod B
              ▲
              │ owned by
        ReplicaSet platform-lab-9c5b867f
              ▲
              │ owned by
        Deployment/platform-lab  (replicas=2, digest sha256:1cca2b59…872ff)
```

Observability (unchanged during experiment):

- Prometheus / Grafana / kube-state-metrics / node-exporter in `monitoring`
- Metrics Server in `kube-system` (HPA path; not the recovery mechanism here)

---

## 3. Baseline State (T0)

| Item | Value |
|---|---|
| Context | `ckad-lab` |
| Nodes | `192.168.56.10/11/12` all Ready |
| Deployment | `platform-lab` **2/2** Ready · image digest `sha256:1cca2b59…872ff` |
| Active ReplicaSet | `platform-lab-9c5b867f` desired/current/ready **2/2/2** |
| Pods | `platform-lab-9c5b867f-r455h`, `platform-lab-9c5b867f-r4666` (both on `k8s-worker-02`) |
| Endpoints | `10.244.118.107:8000`, `10.244.118.125:8000` (**2**) |
| HPA | min=2 max=4 replicas=2 · cpu ~4%/70% |
| PDB | `minAvailable: 1` · allowed disruptions=1 |
| `/health` | HTTP **200** |
| `/version` | **0.1.4** HTTP 200 |
| Prometheus `up{job="platform-lab"}` | **2** UP (both pods) |
| KSM | `spec_replicas=2`, `status_replicas_available=2` |
| Argo CD `platform-lab-local` | **Synced / Healthy** |

No CrashLoopBackOff / OOMKilled / Pending / MemoryPressure at baseline.

---

## 4. Failure Injection

| Field | Value |
|---|---|
| Selected pod | `platform-lab-9c5b867f-r455h` |
| Ownership verified | `ReplicaSet/platform-lab-9c5b867f` · label `app.kubernetes.io/name=platform-lab` |
| Exact command | `kubectl delete pod platform-lab-9c5b867f-r455h -n platform-lab` |
| Pods deleted | **1** (only) |
| Other mutations | **None** |

---

## 5. Kubernetes Recovery Sequence

Observed timeline (wall clock from delete command return ~`10:39:30.6`):

| Step | Approx elapsed | Observation |
|---|---|---|
| Delete issued | 0.0s | API accepts deletion |
| Available replicas drop | ≤1s | Deployment `available=1`; Endpoints **1** |
| Replacement created | **~0.2s** | Pod `platform-lab-9c5b867f-dfd2m` appears (`Pending`) |
| Replacement Running | **~2.5s** | Container started on `k8s-worker-01` |
| Victim not-ready | ~4s | Victim readiness false while Terminating |
| Replacement Ready | **~10.4s** | readiness probe passes |
| Available replicas recover | **~10.4s** | Deployment `available=2` |
| Endpoints recover | **~10.4s** | Endpoints **2** (survivor + replacement) |
| Prometheus sees new target UP | ≤**~65s*** | `up{job="platform-lab"}` includes `…-dfd2m` |

\*Prometheus was polled after the watch loop ended (~65s). With a **30s** scrape interval, discovery is expected shortly after Ready; the **65s** figure is an upper bound from when we queried, not the exact scrape instant.

Survivor pod `…-r4666` remained Ready throughout.

---

## 6. Deployment → ReplicaSet → Pod Relationship

```text
Deployment/platform-lab
  desired replicas = 2   (unchanged in Git / spec)
        │
        ▼
ReplicaSet/platform-lab-9c5b867f
  detects current pods < desired
  creates platform-lab-9c5b867f-dfd2m
        │
        ▼
Pods: r4666 (survivor) + dfd2m (replacement)
```

**Important:** deleting a Pod does **not** modify the Deployment object. The controller stack restores the **declared** replica count.

Final RS status: desired/current/ready **2/2/2**.

---

## 7. Service / Endpoint Behavior

| Phase | Endpoint count | Notes |
|---|---|---|
| Before | 2 | Both original pods |
| During | 1 | Victim removed from Endpoints when not Ready / terminating path |
| After Ready | 2 | `10.244.118.107:8000` (survivor) + `10.244.36.233:8000` (replacement) |

Bounded `/health` polling (~0.5s interval, ~40 samples) during recovery: **all HTTP 200**. No observed client-visible outage through ingress for this single-pod failure (one healthy backend remained).

---

## 8. kube-state-metrics Observation

Verified metrics before/after:

| Metric | Before | After recovery |
|---|---|---|
| `kube_deployment_spec_replicas{deployment="platform-lab"}` | 2 | 2 |
| `kube_deployment_status_replicas_available{...}` | 2 | 2 |
| `count(kube_pod_info{namespace="platform-lab"})` | 2 | 2 (once Terminating object fully removed) |

Conceptual mid-failure state (from Deployment status polls):

```text
desired = 2
available = 1   (briefly)
→ available = 2
```

**Limitation:** with ~0.4–1s polling and Prometheus scrape cadence, a continuous Grafana time-series of the 1→2 dip may be short; the Deployment status polls captured `available=1` clearly for ~10s.

---

## 9. Prometheus Observation

| Phase | `up{job="platform-lab"}` |
|---|---|
| Before | 2 UP (`r455h`, `r4666`) |
| After recovery (measured) | 2 UP (`r4666`, `dfd2m`) |

- Deleted pod target disappears from active scrape set as the endpoint vanishes.
- Survivor stays UP.
- Replacement appears as a **new** target (`instance` = new pod IP).
- Discovery latency is bounded by ServiceMonitor interval (**30s**) plus endpoint readiness.

---

## 10. Grafana Observation

Used existing **Kubernetes Platform VMware** dashboard (no dashboard edits).

Expected panels that reflect this experiment:

- Available replicas / desired vs available (KSM)
- App availability / `up{job="platform-lab"}`
- HTTP request rate (continued via remaining pod)
- Pod count

**Limitation:** a brief ~10s available-replica dip may appear as a thin notch or be undersampled depending on scrape/step; the controller behavior is still proven via kubectl timing logs.

---

## 11. HPA Behavior

| Check | Result |
|---|---|
| HPA config changed? | **No** |
| Manual scale? | **No** |
| HPA caused replacement? | **No** |
| After event | still min=2 max=4 · current/desired **2/2** · cpu ~4%/70% |

Replacement was created by the **ReplicaSet** controller to satisfy Deployment `.spec.replicas`, not by HPA.

---

## 12. PDB Behavior

PDB `platform-lab`: `minAvailable: 1`, allowed disruptions = 1.

This experiment used **direct** `kubectl delete pod`, which is **not** an eviction API path. PDB primarily gates **voluntary disruptions** (drain/eviction). It did **not** block this delete, and it was **not** the recovery mechanism.

Recovery still left ≥1 Ready pod almost immediately (survivor), satisfying the PDB’s availability intent operationally.

---

## 13. Argo CD Behavior

| Application | Status after experiment |
|---|---|
| `platform-lab-local` | **Synced / Healthy** |

Why deleting a Pod does **not** imply Argo OutOfSync:

1. Git desired state is the **Deployment** (and related objects), not individual Pod names.
2. ReplicaSet maintains Pod count to match Deployment.
3. Argo reconciles Git manifests ↔ live API objects for managed resources; ephemeral Pod identities are expected to churn.

**Kubernetes self-healing ≠ Argo CD self-healing**

| Mechanism | What it heals |
|---|---|
| Deployment/ReplicaSet | Missing Pods vs `.spec.replicas` |
| Argo CD | Drift of Git-managed objects (Deployments, Services, …) vs Git |

This experiment exercised the **Kubernetes controller** path only.

---

## 14. Recovery Timing

| Milestone | Approx duration from delete |
|---|---|
| Failure detected (available→1 / endpoints→1) | ≤ **1s** |
| Replacement Pod created | **~0.2s** |
| Replacement Running | **~2.5s** |
| Replacement Ready | **~10.4s** |
| Available replicas back to 2 | **~10.4s** |
| Endpoints back to 2 | **~10.4s** |
| Prometheus replacement target UP (first measured) | ≤ **~65s** (upper bound; scrape interval 30s) |

---

## 15. Final State

| Item | Result |
|---|---|
| Deployment | **2/2** Ready · same digest |
| Running pods | `…-r4666`, `…-dfd2m` |
| Endpoints | 2 healthy |
| `/health` / `/version` | 200 / `0.1.4` |
| HPA / PDB | unchanged / healthy |
| Nodes | Ready |
| Prometheus / Grafana / KSM / node-exporter / Metrics Server | healthy |
| Argo `platform-lab-local` | Synced / Healthy |
| OOM / eviction / MemoryPressure | **none** observed for this experiment |

### Additional observation: slow Terminating cleanup

The deleted pod remained in **Terminating** for several minutes after Ready recovery. `kubectl describe` showed:

```text
FailedKillPod … KillPodSandboxError … plugin type="calico" failed (delete):
error getting ClusterInformation: connection is unauthorized: Unauthorized
```

- Container stop completed (`reason: Completed`).
- Sandbox network teardown failed (Calico authorization).
- **Self-healing still succeeded**: new Pod Ready, Service had 2 endpoints, app healthy.
- This is a **node/CNI cleanup** issue, not a Deployment controller failure.
- Grace period configured: **30s**; stuck beyond that due to sandbox kill errors.
- No force-delete was performed (would be an extra mutation).

---

## 16. Lessons Learned

1. Deleting a Pod is temporary; controllers restore desired replica count.
2. Service stays available if ≥1 Ready endpoint remains (PDB intent aligns).
3. HPA was a spectator; ReplicaSet did the heal.
4. Argo stayed Synced because Git-level objects did not drift.
5. Observability (KSM + Prometheus `up`) can show the dip/recovery; scrape resolution may blur sub-interval events.
6. Pod **Terminating** stuck ≠ application unrecovered — always check Deployment available replicas and Endpoints.

---

## 17. Extended Failure Visibility Experiment

**Date:** 2026-09-26 (same day, second controlled run)  
**Goal:** Make the `available replicas 2 → 1 → 2` transition visible to Prometheus/Grafana given a **30s** scrape interval.

### Why the first ~10.4s failure was hard to see in Grafana

| Layer | What happened in experiment 1 |
|---|---|
| Kubernetes | Available dipped to 1 for ~10s (real) |
| Prometheus | Scrape interval **30s** → at most ~0–1 samples can land in the dip |
| Grafana | Charts step/lookback often miss a sub-interval notch |

**Lesson:** short outages can be real in Kubernetes yet nearly invisible in dashboards.

### Method (safe, temporary scheduling delay)

1. **Cordon** workers only: `k8s-worker-01`, `k8s-worker-02` (no drain).
2. Confirm control-plane taint `node-role.kubernetes.io/control-plane:NoSchedule` (apps cannot schedule there).
3. Delete **exactly one** Running app pod: `platform-lab-9c5b867f-r4666`.
4. Replacement stays **Pending** (~85–90s) while workers are unschedulable.
5. **Uncordon** both workers (mandatory cleanup).
6. Replacement schedules → Running → Ready → available returns to 2.

No Deployment/HPA/PDB/Prometheus/Grafana/Git changes. AWS untouched.

### Timing diagram (measured)

```text
T0  ~10:54:20  Baseline available=2, endpoints=2, health=200
T1  ~10:54:21  Deleted platform-lab-9c5b867f-r4666
T2  ~10:54:21  Kubernetes available=1, endpoints=1
T3  ~10:54:21  Replacement platform-lab-9c5b867f-65xpb Pending
               FailedScheduling: 2 unschedulable workers + control-plane taint
T4  ~10:54:51  Prometheus/KSM first scraped available=1  (≈30s after T2)
               … continued available=1 samples …
T5  ~10:55:51  Workers uncordoned (Pending held ≈90s from T3)
T6  ~10:55:55  Replacement Running (~3s after uncordon)
T7  ~10:56:02  Replacement Ready (~10s after uncordon)
T8  soon after Deployment available=2; KSM caught up to 2 by later query
```

### Three layers of “truth”

| Layer | Observation during failure window |
|---|---|
| **Kubernetes actual state** | `availableReplicas=1` for entire ~85s window; endpoints=1; replacement Pending |
| **Prometheus sampled state** | `kube_deployment_status_replicas_available` stayed **2** for first ~30s (stale scrape), then **1** across multiple scrapes |
| **Grafana visualization** | With Last 15m on **Kubernetes Platform VMware**, Available replicas should show a sustained valley **2 → 1 → 2**; Desired stays **2** |

### Prometheus evidence (query_range, step=15s)

Metric:

```promql
kube_deployment_status_replicas_available{namespace="platform-lab",deployment="platform-lab"}
```

| Local time | available |
|---|---|
| 10:54:21 | 2 |
| 10:54:36 | 2 |
| 10:54:51 | **1** |
| 10:55:06 | **1** |
| 10:55:21 | **1** |
| 10:55:36 | **1** |
| 10:55:51 | **1** |
| 10:56:06 | **1** (scrape lag vs Ready at ~10:56:02) |

- Samples with `available=1` in this range: **6** (15s step)  
- Instant polls during Pending with `ksm_available=1`: **11**  
- Instant Kubernetes polls with `available=1`: **16** (entire observation window)

Scrape interval remains **30s** (unchanged).

### Application continuity

| Check | Result |
|---|---|
| Surviving pod | `platform-lab-9c5b867f-dfd2m` (worker-01) |
| `up{job="platform-lab"}` during failure | survivor stayed **1**; deleted target eventually disappeared |
| Endpoints during failure | **1** |
| `/health` during failure | **HTTP 200** on every bounded poll |
| Desired replicas | **2** unchanged |

### Recovery after uncordon

| Event | Approx |
|---|---|
| Uncordon both workers | 10:55:51 |
| Replacement Running | +~3.0s |
| Replacement Ready | +~10.2s |
| Final Deployment | **2/2** Ready |
| Final endpoints | 2 (`dfd2m` + `65xpb`) |
| Final `/health` `/version` | 200 / **0.1.4** |
| Image digest | unchanged `sha256:1cca2b59…872ff` |
| Nodes | Ready, **no** SchedulingDisabled |
| Argo `platform-lab-local` | Synced / Healthy |

### Grafana result

Prometheus stored a multi-minute `available=1` plateau. On dashboard **Kubernetes Platform VMware** (Last 15 minutes), the Available-replicas panel is expected to show **2 → 1 → 2**. Desired-replicas stays flat at **2**.

If a panel still looks flat, check raw PromQL in Explore first (table above) — do **not** change scrape interval or dashboards for this lab. Likely causes would be panel time range, wrong labels, or `min`/`max` over a wide step — not absence of the metric.

### Safety confirmations

- Workers were **uncordoned** before finish.
- Exactly **one** Running app pod deleted in this experiment (`r4666`).
- No permanent cluster/Git config changes (docs only).
- Temporary `FailedScheduling` on the Pending pod was **expected** and cleared after uncordon.

---

## 18. Readiness Failure and Service Traffic Isolation

**Date:** 2026-09-26 (same lab day as experiments 1–2)  
**Type:** Controlled readiness failure (no pod delete, no Deployment change)  
**AWS:** not modified  

### Why readiness failure ≠ pod failure

| | Pod delete (exps 1–2) | Readiness failure (this) |
|---|---|---|
| Pod object | Deleted | **Same pod remains** |
| Container | Gone | Stays present (frozen / non-responsive) |
| Phase | Terminating → new Pod | Stays **Running** |
| Ready | n/a → new Ready | **True → False → True** |
| ReplicaSet | Creates **replacement** Pod | Desired/current stay **2**; **no new Pod** |
| Service | Endpoint removed (pod gone) | Endpoint removed (**NotReady**) |
| Recovery | New container start | Process resume **or** same-pod container restart |

```text
Pod A                         Pod B
Running + Ready               Running + Ready
      ↓
FastAPI / container suspended (Pod A only)
      ↓
Running + NOT Ready           Running + Ready
      ↓
Removed from Service endpoints
      ↓
Traffic only to Pod B
      ↓
Process / container resumed (same Pod A)
      ↓
Running + Ready
      ↓
Endpoint restored
```

**Running ≠ Ready.** A Pod can remain Running while Kubernetes refuses it as a Service endpoint.

### How the experiment was performed

1. **Baseline:** `platform-lab` 2/2 Ready · endpoints 2 · digest `sha256:1cca2b59…872ff` · `/health` 200 · `/version` 0.1.4.
2. **Selected pod:** `platform-lab-9c5b867f-65xpb` on `k8s-worker-01` (container `platform-lab`).
3. **PID identity:** `/proc/1/cmdline` = `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000` → FastAPI/uvicorn is **PID 1**.
4. **SIGSTOP attempt (failed on PID 1):**
   - `bash -c 'kill -STOP 1'` and `os.kill(1, SIGSTOP)` return success but `/proc/1/status` stays `S (sleeping)`.
   - Same `kill -STOP` on a **child** process correctly yields `T (stopped)`.
   - Container **PID 1** does not accept SIGSTOP from inside the namespace (init / unkillable semantics). Per lab rules, Deployment/probe edits were **not** used as a substitute.
5. **Working suspension:** on `k8s-worker-01`:
   ```bash
   sudo ctr -n k8s.io tasks pause <containerID>
   # hold ~75s
   sudo ctr -n k8s.io tasks resume <containerID>   # best-effort; see liveness note
   ```
   Container ID (this run): `b362844ded38f…e0f7`. Task status became **PAUSED**. Processes remain; they do not answer HTTP.

### Readiness probe (unchanged)

| Field | Value |
|---|---|
| Path / port / scheme | `/health` · named port `http` · HTTP |
| initialDelaySeconds | 3 |
| periodSeconds | 10 |
| timeoutSeconds | 2 |
| failureThreshold | 3 |
| successThreshold | 1 |

After three consecutive timeouts, kubelet sets Ready=False. Liveness uses the **same** `/health` path with period **15s** / failureThreshold **3** (relevant to recovery path below).

### Observed timing

| Event | Elapsed |
|---|---|
| `ctr tasks pause` | T0 (~05:55:19Z) |
| Still Running+Ready (failures accumulating) | 0–~30s |
| **NotReady** + endpoints **1** + available **1** | **~31.5 s** |
| Hold while NotReady | through **~73 s** |
| Recovery to 2/2 Ready + 2 endpoints | **~5.9 s** after resume/recovery start |

### Kubernetes state during failure

| Item | Before | During | After |
|---|---|---|---|
| Selected pod | Running 1/1 | **Running 0/1** | Running 1/1 (restartCount **1**) |
| Other pod (`dfd2m`) | Running 1/1 | Running 1/1 | Running 1/1 |
| Deployment desired | 2 | **2** | 2 |
| Deployment available | 2 | **1** | 2 |
| Active RS `…-9c5b867f` | 2/2/2 | **2 current / 1 ready** (no extra Pod) | 2/2/2 |
| Endpoints | 2 | **1** (`10.244.36.233` only) | 2 |

**Probe failure message (actual):**

```text
Readiness probe failed: Get "http://10.244.36.194:8000/health":
  context deadline exceeded (Client.Timeout exceeded while awaiting headers)
Liveness probe failed: Get "http://10.244.36.194:8000/health":
  context deadline exceeded (Client.Timeout exceeded while awaiting headers)
```

### Service traffic

- Before endpoint removal, a few ingress checks returned **`000`** (timeout) when traffic landed on the paused pod — expected race.
- After Ready=False / endpoints=1, bounded `/health` checks returned **HTTP 200** via the survivor.
- `/version` final: **0.1.4**. Digest unchanged.

### Deployment / ReplicaSet

Desired replicas stayed **2**. ReplicaSet **did not** create a third pod: the NotReady pod still counts toward `replicas` / `current`. Available replicas dropped because Ready≠Running.

### KSM / Prometheus

| Metric / PromQL | Observation |
|---|---|
| `kube_pod_status_ready{namespace="platform-lab",condition="true",pod="…-65xpb"}` | **1 → 0 → 1** |
| `kube_deployment_status_replicas_available{namespace="platform-lab",deployment="platform-lab"}` | **2 → 1 → 2** |
| Samples with available=1 / ready=0 (15s step) | **4** each in the captured window (~05:55:50–05:56:35Z) |
| `up{job="platform-lab"}` for `65xpb` | **1 → 0 → 1** (direct pod scrape timed out while frozen; **not** the same as Service endpoint removal) |
| `up` for `dfd2m` | stayed **1** |

Scrape interval remains **30s** (unchanged).

### Grafana

On **Kubernetes Platform VMware** (Last 15 minutes), expect:

- Available replicas: **2 → 1 → 2**
- Desired replicas: flat **2**
- Application availability (Service path): mostly UP after isolation

Pod-level readiness may need Explore/`kube_pod_status_ready` if the dashboard lacks a dedicated readiness panel — **do not** edit the dashboard in this milestone.

### HPA / PDB / Argo

| Controller | Role in this experiment |
|---|---|
| HPA | Unchanged · did **not** create pods for NotReady |
| PDB | Unchanged · did **not** restore readiness |
| Argo CD `platform-lab-local` | Remained **Synced / Healthy** · not a Git drift event |

Readiness is a **kubelet / Endpoints** runtime health path, not GitOps reconciliation.

### Recovery note (liveness interaction)

Holding NotReady ~60–90s overlaps the **liveness** budget (3×15s). In this run the selected pod’s **restartCount went 0 → 1**: kubelet restarted the **same** pod’s container after liveness timeouts. That is still **not** ReplicaSet replacement (same pod name; RS current stayed 2). `ctr resume` was attempted; final Ready came from the restarted container answering `/health` again.

### Limitations

- In-container **SIGSTOP to PID 1** is ineffective on this image/runtime; node-level `ctr tasks pause` was required.
- Shared `/health` for readiness **and** liveness means a long freeze can become a **container restart**, not only NotReady.
- Brief ingress timeouts can appear **before** endpoint removal while probes are still accumulating failures.
- Not a Deployment/probe redesign, not pod delete, not Argo drift, not AWS.

---

## 19. Limitations (summary)

- Single-pod failure with one survivor; not a full outage.
- Experiment 1’s ~10s dip can be invisible at 30s scrape cadence.
- Experiment 2 uses temporary cordon (scheduling delay), not production node failure.
- Experiment 3 (readiness): PID 1 SIGSTOP blocked; pause + liveness overlap can restart the same container.
- Calico sandbox cleanup can leave old pods Terminating long after healthy replacements exist.
- Not an HPA, Argo drift, rollout, or real node-crash test.

---

## 20. Next Failure Experiment

Candidates for later milestones (separate):

- True node failure / drain with PDB interaction
- Multi-pod disruption vs PDB
- Bad image / CrashLoopBackOff recovery
- AWS parity of single-pod / readiness labs
- Optional: separate readiness vs liveness paths for cleaner freeze demos (would be a **config** change — out of scope here)

---

## Appendix — Commands used

```powershell
kubectl config current-context   # ckad-lab
kubectl get deploy,rs,pods,svc,endpoints,hpa,pdb -n platform-lab -o wide
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/version

# Experiment 1 — fast self-heal:
kubectl delete pod platform-lab-9c5b867f-r455h -n platform-lab

# Experiment 2 — extended visibility (temporary):
kubectl cordon k8s-worker-01
kubectl cordon k8s-worker-02
kubectl delete pod <one-running-platform-lab-pod> -n platform-lab
# observe Pending ~75–90s, then ALWAYS:
kubectl uncordon k8s-worker-01
kubectl uncordon k8s-worker-02

# Experiment 3 — readiness (SIGSTOP to PID 1 is a no-op; use node pause):
# on k8s-worker-01, container ID from:
#   kubectl get pod <pod> -n platform-lab -o jsonpath='{.status.containerStatuses[0].containerID}'
ssh k8s-worker-01 "sudo ctr -n k8s.io tasks pause <containerID>"
# observe Running 0/1, endpoints 1, then ALWAYS:
ssh k8s-worker-01 "sudo ctr -n k8s.io tasks resume <containerID>"

kubectl get pods -n platform-lab -o wide
kubectl get deploy,endpoints -n platform-lab
kubectl get application platform-lab-local -n argocd
```
