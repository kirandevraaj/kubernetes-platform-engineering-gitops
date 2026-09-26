# VMware Kubernetes Worker Node Failure and Resilience

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Experiment type:** Single worker kubelet outage (heartbeat / NotReady path) — not `kubectl drain`  
**AWS:** not modified (no AWS kubecontext available on this workstation for live check; overlays/app left at known-good `0.1.4`)  

---

## 1. Objective

Demonstrate platform behavior when **one** Kubernetes worker becomes unavailable:

```text
Healthy cluster
    ↓
One worker fails (kubelet stopped)
    ↓
Node Ready → Unknown / NotReady + unreachable taints
    ↓
Application capacity reduced (available 2 → 1)
    ↓
Service endpoints 2 → 1
    ↓
(Replacement eviction may wait on NoExecute toleration ~300s)
    ↓
Worker restored (kubelet started)
    ↓
Node Ready, taints cleared, endpoints 2, app healthy
```

---

## 2. Cluster Topology

| Node | Role | IP |
|---|---|---|
| `k8s-ctrl-01` | control-plane | 192.168.56.10 |
| `k8s-worker-01` | worker | 192.168.56.11 |
| `k8s-worker-02` | worker (**failed**) | 192.168.56.12 |

Application: `platform-lab` Deployment · replicas **2** · digest `sha256:1cca2b59…872ff` · version **0.1.4**  
Strategy: RollingUpdate `maxUnavailable: 0` / `maxSurge: 1`  
Topology: soft `topologySpreadConstraints` (`ScheduleAnyway`) on `kubernetes.io/hostname`

---

## 3. Baseline

### Placement prep (required for safety gate)

Initially **both** Ready app pods were on `k8s-worker-01` (spread not achieved). Failing that worker would have taken out all application capacity — forbidden by the safety model.

Prep (not the failure mechanism):

1. Deleted one co-located Ready pod so the ReplicaSet could reschedule with skew preference.
2. Replacement initially stuck `ContainerCreating` on `k8s-worker-02` due to Calico CNI `Unauthorized` (same class of issue as lingering Terminating pods).
3. Restarted Calico components on `k8s-worker-02` only; sandbox create succeeded afterward.

**Pre-failure placement:**

| Pod | Node | Ready |
|---|---|---|
| `platform-lab-9c5b867f-65xpb` | `k8s-worker-01` | 1/1 |
| `platform-lab-9c5b867f-rhnrf` | `k8s-worker-02` | 1/1 |

| Check | Value |
|---|---|
| Endpoints | **2** |
| `/health` | **200** |
| `/version` | **0.1.4** |
| PDB | minAvailable=1 · currentHealthy=2 · disruptionsAllowed=1 |
| HPA | min=2 max=4 · replicas=2 |
| Argo `platform-lab-local` | Synced / Healthy |
| Nodes | all Ready · no Memory/Disk/PID pressure |

Selected failure target: **`k8s-worker-02`** (exactly one app pod).

---

## 4. Failure Injection Method

**Mechanism:** SSH to worker → `sudo systemctl stop kubelet`

This is a **kubelet / node-heartbeat failure simulation**, not a VMware VM power-off (no safe VM power API used from this workstation).

**Not used:** `kubectl drain`, cordon-as-failure, control-plane touch, dual-worker failure, manual app pod delete during the outage window.

**Reversal:** `sudo systemctl start kubelet` (executed; kubelet left `active`).

---

## 5. Node Failure Detection

| Event | Approx time from kubelet stop |
|---|---|
| Failure start (T0) | **~2026-09-26T06:33:38Z** |
| Ready condition → **Unknown** (NotReady in `kubectl get nodes`) | **~42.7 s** |
| Endpoint count 2 → 1 | **~42.7 s** (same poll) |
| Available replicas 2 → 1 | **~42.7 s** |

Kubernetes reports the Ready condition status as **`Unknown`** (reason typically node status heartbeat loss), which `kubectl get nodes` surfaces as **NotReady**.

---

## 6. Node Conditions and Taints

Observed taints after loss of kubelet heartbeats:

| Taint key | Effect | When observed |
|---|---|---|
| `node.kubernetes.io/unreachable` | **NoSchedule** | ~42.7 s |
| `node.kubernetes.io/unreachable` | **NoExecute** | ~51.7 s |

No MemoryPressure / DiskPressure / PIDPressure introduced by the experiment.

Default Pod toleration for unreachable NoExecute is **300 seconds** — important for eviction timing (see §8).

---

## 7. Application Impact

| Metric | Before | During | After restore |
|---|---|---|---|
| Available replicas | 2 | **1** | 2 |
| Endpoints | 2 | **1** (survivor `10.244.36.194`) | 2 |
| Victim pod `…-rhnrf` | Ready | Running + **Ready=False** (still listed on failed node) | Ready again |
| Survivor `…-65xpb` | Ready | Ready on worker-01 | Ready |
| PDB currentHealthy | 2 | **1** | 2 |

External `/health` checks via ingress VIP often returned **`000`** (connection failure) during the outage even while the survivor pod remained Ready and one Service endpoint existed. Likely interaction: ingress / MetalLB announcement path affinity to the failed worker — **Kubernetes Pod Ready ≠ external path healthy**. After restore, `/health` returned **200** again.

---

## 8. Pod Eviction / Rescheduling

**Within the observed outage window (~5+ minutes of NotReady/Unknown before restore):**

- Victim pod remained associated with `k8s-worker-02` (not deleted).
- **No replacement Pod** was created by the ReplicaSet.
- Desired replicas stayed **2**; current still counted the not-ready victim.

**Why:** NoExecute taint-based eviction waits for the default **300s** toleration after the unreachable NoExecute taint appears (~51s). Restore occurred **before** that eviction deadline completed, so Kubernetes never forced a reschedule in this run.

This is a core distinction from **pod delete** self-healing (immediate RS replacement).

---

## 9. Service Endpoint Behavior

Endpoints dropped from **2 → 1** as soon as the victim became unready / node unreachable (~42.7s). Survivor endpoint retained. After kubelet restore, endpoints returned to **2**.

---

## 10. PDB Behavior

| Field | During failure |
|---|---|
| minAvailable | 1 |
| currentHealthy | **1** |
| desiredHealthy | 1 |
| disruptionsAllowed | 0 or reduced vs baseline |

PDB did **not** prevent involuntary node failure effects. PDBs govern **voluntary** disruptions (drain/eviction API). This experiment was involuntary (kubelet stop).

---

## 11. kube-state-metrics Observation

PromQL:

```text
kube_deployment_status_replicas_available{namespace="platform-lab",deployment="platform-lab"}
```

Prometheus range (15s step) showed a multi-minute plateau of **`available=1`** (approx **06:35:04–06:39:34Z**), then return to **`2`** after recovery (~**06:39:49Z**).

Also relevant: `kube_pod_status_ready` for the victim falling to not-ready while phase remained Running.

---

## 12. node-exporter Observation

`up{job="node-exporter"}` for `192.168.56.12:9100` did not show a sustained down plateau in the short query_range window captured after recovery (last sample `1`). Node-exporter scrape status and Kubernetes Node Ready are **related but not identical timelines** — kubelet NotReady can precede or outlast exporter target state depending on scrape timing and whether the node IP remains reachable while kubelet is down (containerd/process network may still answer :9100 briefly or metrics path differs).

Documented expectation for longer outages: exporter target for the failed worker becomes **0** or disappears from discovery.

---

## 13. Prometheus Observation

| Series | Behavior |
|---|---|
| Deployment available | **2 → 1 → 2** (captured) |
| Application `up{job="platform-lab"}` | Survivor stayed scrapeable; victim target degraded/absent depending on discovery |
| Scrape interval | 30s (unchanged) |

---

## 14. Grafana Observation

Dashboard **Kubernetes Platform VMware** (Last 15m) should show available replicas **2 → 1 → 2** matching the PromQL plateau above. Node panels may show worker-02 unhealthy while Ready=Unknown. Do not modify dashboards for this lab.

---

## 15. Recovery

| Step | Action / result |
|---|---|
| Restore | `sudo systemctl start kubelet` on `k8s-worker-02` |
| Kubelet | `active` / `enabled` |
| Node | Ready condition True (`KubeletReady`); unreachable taints cleared |
| App | victim Ready again · endpoints **2** · available **2** |
| `/health` `/version` | **200** / **0.1.4** |
| Image digest | unchanged `sha256:1cca2b59…872ff` |
| Argo | Synced / Healthy (did not drive node recovery) |

---

## 16. Timing Measurements

| Milestone | Time |
|---|---|
| T0 kubelet stop | ~06:33:38Z |
| T1 Ready=Unknown / NotReady | **~42.7 s** |
| T2 capacity/endpoints affected | **~42.7 s** |
| T3 eviction/replacement begin | **not reached** before restore (NoExecute + 300s) |
| T4–T6 replacement schedule/Ready/endpoints via new pod | **n/a this run** |
| T7 node restored | kubelet start ~06:39Z local experiment clock; full Ready + ep=2 + health 200 shortly after |

---

## 17. Kubernetes Self-Healing vs Node Recovery

| Layer | Role here |
|---|---|
| kubelet heartbeat + node controller | Detected Unknown/NotReady; applied unreachable taints |
| Endpoint controller | Removed unready victim from Service |
| ReplicaSet | Would replace only after NoExecute eviction removes the pod object |
| PDB | Did not block involuntary failure |
| Argo CD | Remained Synced; **did not** restart kubelet or heal the node |
| Human/lab action | Restarted kubelet to restore the worker |

---

## 18. Lessons Learned

1. **Pod failure ≠ node failure.** Delete → fast RS replace. Node loss → NotReady + taints; reschedule delayed by NoExecute toleration (~300s).
2. **Voluntary vs involuntary.** Drain/PDB vs kubelet stop — PDB does not “save” you from node death.
3. **Ready condition may be `Unknown`**, not only `False`.
4. **Spread matters.** Both pods on one worker would have meant total app loss for that worker failure.
5. **External availability can break** even with a Ready survivor if ingress/LB paths depend on the failed node.
6. **Calico health on a worker** can block reschedule onto that node until CNI auth is healthy.

---

## 19. Limitations

- Used kubelet stop, not full VM power loss.
- Observation window ended before 300s NoExecute eviction produced a replacement pod.
- External `/health` returned `000` during failure — survivor Ready but VIP/ingress path degraded; root-cause beyond MetalLB/ingress affinity not fully dissected.
- node-exporter down plateau not strongly captured post-facto in the recovered query window.
- Prep required one pod delete + Calico pod restarts on worker-02 (documented; not permanent config).

---

## 20. Next Resilience Experiment

Candidates:

- Longer outage past **300s** NoExecute to capture forced eviction + reschedule onto the surviving worker
- True VM power-off if VMware automation is available
- Control-plane HA / etcd loss (separate, higher risk)
- Combined node failure + PDB drain comparison lab

---

## Appendix — Commands

```powershell
kubectl config current-context   # ckad-lab
kubectl get nodes -o wide
kubectl get pods -n platform-lab -o wide

# Failure (reversible):
ssh k8s-worker-02 "sudo systemctl stop kubelet"

kubectl get nodes -w
kubectl get pods -n platform-lab -o wide
kubectl get endpoints -n platform-lab

# ALWAYS restore:
ssh k8s-worker-02 "sudo systemctl start kubelet"
kubectl get nodes
```
