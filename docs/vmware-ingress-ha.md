# VMware ingress-nginx High Availability

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Scope:** ingress-nginx HA only (replicas, topology spread, PDB) via GitOps  
**Application:** platform-lab **0.1.4** · digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` (unchanged)

---

## 1. Problem Discovered

During a prior worker-02 kubelet outage, `platform-lab` retained one Ready Pod and one Service endpoint on worker-01, yet external HTTP through MetalLB VIP `192.168.56.200` failed.

Root cause: **ingress-nginx had a single replica**, scheduled only on the failed worker. The ingress Service lost all Ready endpoints even though the application survivor was healthy.

---

## 2. Original Single-Replica Architecture

| Item | Before HA |
|---|---|
| Namespace | `ingress-nginx` |
| Deployment | `ingress-nginx-controller` |
| Service | `ingress-nginx-controller` (LoadBalancer → `192.168.56.200`) |
| Replicas | **1** |
| Placement | **worker-02 only** |
| PDB | none |
| Topology spread | none |
| Ownership | Helm chart `ingress-nginx` **4.15.1**; Argo `platform-lab-local` owned only the Service MetalLB patch |

---

## 3. Failure Evidence

From the networking anatomy investigation and node-failure lab:

- worker-02 NotReady → sole ingress Pod unavailable → ingress Ready endpoints **1 → 0**
- platform-lab endpoints **2 → 1** (survivor remained)
- External `/health` via VIP often returned connection failure (`000`)
- Internal app health on the survivor remained OK

Confirmed SPOF: **single ingress replica on a single worker**.

---

## 4. HA Design

Target:

- **2** ingress-nginx controller replicas
- Soft spread across the two workers
- PDB `minAvailable: 1` for voluntary disruptions
- GitOps as source of truth (no permanent `kubectl patch` / `kubectl edit`)
- Soft scheduling so a single remaining worker can still run both replicas if needed during recovery

Git objects (Argo Application `platform-lab-local` → `kubernetes/overlays/local`):

| File | Purpose |
|---|---|
| `ingress-nginx-controller-ha.yaml` | Deployment desired state: `replicas: 2` + topology spread |
| `ingress-nginx-controller-pdb.yaml` | PDB `minAvailable: 1` |
| `ingress-nginx-controller-service.yaml` | Existing MetalLB LoadBalancer Service (unchanged) |
| `ingress-nginx-values.yaml` | Documented Helm values so a future `helm upgrade` does not revert HA |

Helm still installed the original release; GitOps now owns HA fields and the Service exposure path without replacing AWS or application overlays.

---

## 5. Replica Placement

After Argo sync (`97cabed`):

| Pod | Node | Ready |
|---|---|---|
| `ingress-nginx-controller-6fd8d676c4-588jm` | **k8s-worker-01** | 1/1 |
| `ingress-nginx-controller-6fd8d676c4-7pqqq` | **k8s-worker-02** | 1/1 |

Ingress Ready endpoints: **2** (one per worker).

---

## 6. Pod Anti-Affinity / Topology Spreading

Mechanism used: **`topologySpreadConstraints`** (same soft pattern as `platform-lab`):

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/component: controller
        app.kubernetes.io/instance: ingress-nginx
        app.kubernetes.io/name: ingress-nginx
```

- Prefers one replica per worker when both are schedulable
- **Does not** use required anti-affinity (avoids unschedulable pods when only one worker remains)
- Node label `kubernetes.io/hostname` verified on all three nodes; control-plane remains unschedulable via `NoSchedule` taint

---

## 7. PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/component: controller
      app.kubernetes.io/instance: ingress-nginx
      app.kubernetes.io/name: ingress-nginx
```

Observed healthy state: `currentHealthy=2`, `desiredHealthy=1`, `disruptionsAllowed=1`.

PDB governs **voluntary** eviction (drain). It does not block involuntary kubelet/node failure; it still encodes the availability intent for upgrades.

---

## 8. MetalLB Interaction

| Item | Value |
|---|---|
| VIP | `192.168.56.200` (pool `lab-pool`) |
| L2Advertisement | `lab-l2` (no nodeSelector) |
| Speakers | 3 (ctrl + both workers) |
| `externalTrafficPolicy` | **Cluster** (unchanged) |

With `Cluster`, kube-proxy may forward VIP/NodePort traffic to **any** Ready ingress Pod, including on a different node than the L2 announcer.

During kubelet-stop tests (node network stack still up), `ServiceL2Status` could still list the failed node briefly while external HTTP continued to succeed — VIP ownership alone is not the availability gate when at least one ingress endpoint remains Ready.

---

## 9. ExternalTrafficPolicy

Left at **`Cluster`**. Changing to `Local` would couple VIP announce node to local endpoints and is a separate networking experiment (see §18).

This HA milestone proves: **surviving ingress capacity** is what restores external availability after a worker loss.

---

## 10. Normal Traffic Path

```text
Windows
  ↓  Host: platform-lab.local
192.168.56.200
  ↓
MetalLB (L2)
  ↓
ingress-nginx Service (LoadBalancer)
  ↓
ingress-01 ─────── worker-01
ingress-02 ─────── worker-02
  ↓
platform-lab Service
  ↓
app pods (2 replicas across workers)
```

---

## 11. Worker-01 Failure Test

**Mechanism:** `sudo systemctl stop kubelet` on `k8s-worker-01` only (VIP announcer at test start).

| Event | Observation |
|---|---|
| T0 stop | `2026-09-26T07:45:14Z` |
| Ingress Ready endpoints | **2 → 1** at ~38s (survivor on **worker-02**) |
| External `/health` (bounded ~90s) | **75 OK / 0 FAIL** |
| `/version` during failure | `0.1.4` |
| Restore | `sudo systemctl start kubelet` @ `07:46:47Z` |
| Post recovery | nodes Ready · ingress 2/2 · 20/20 health OK |

```text
worker-01 ❌
  ↓
ingress on worker-01 unavailable
MetalLB / Service (Cluster)
  ↓
ingress on worker-02 ✅
  ↓
platform-lab survivor(s)
  ↓
/health 200
```

---

## 12. Worker-02 Failure Test

**Mechanism:** `sudo systemctl stop kubelet` on `k8s-worker-02` only.

| Event | Observation |
|---|---|
| T0 stop | `2026-09-26T07:39:35Z` |
| Ingress Ready endpoints | **2 → 1** at ~36s (survivor on **worker-01**) |
| External `/health` (bounded ~90s) | **75 OK / 0 FAIL** |
| `/version` during failure | `0.1.4` |
| VIP announcer | remained worker-01 (same node as surviving ingress) |
| Restore | kubelet start @ `07:41:09Z` |
| Post recovery | nodes Ready · ingress 2/2 · 20/20 health OK |

```text
worker-02 ❌
  ↓
ingress-02 ❌

MetalLB / Service
  ↓
ingress-01 ✅ (worker-01)
  ↓
platform-lab
  ↓
healthy app
```

---

## 13. External Availability Results

| Test | Requests | Success | Failure | Measured interrupt |
|---|---|---|---|---|
| Baseline (pre-failure) | 30 | 30 | 0 | — |
| worker-02 kubelet stop | ~75 | **75** | **0** | none observed in sample |
| worker-01 kubelet stop | ~75 | **75** | **0** | none observed in sample |
| Post-recovery checks | 20+20 | 40 | 0 | — |

**Acceptance met:** a single worker failure no longer removes all ingress capacity; external `/health` stayed 200 in these kubelet-stop samples.

This does **not** claim zero packet loss for every failure mode (for example full VM power-off / NIC down may still show brief MetalLB/ARP convergence loss).

---

## 14. Recovery

For each test:

1. `sudo systemctl start kubelet` on the failed worker  
2. Node returned **Ready** (not SchedulingDisabled)  
3. Second ingress replica returned to Ready; endpoints **2**  
4. platform-lab endpoints returned to **2**  
5. External `/health` and `/version` validated  

---

## 15. Before vs After

| Metric | Before HA | After HA |
|---|---|---|
| ingress replicas | 1 | **2** |
| ingress nodes | worker-02 only | **worker-01 + worker-02** |
| ingress Ready endpoints | 1 | **2** |
| PDB | none | **minAvailable: 1** |
| VIP | 192.168.56.200 | 192.168.56.200 (unchanged) |
| platform-lab endpoints | 2 | 2 (unchanged) |
| worker-01 failure external availability | N/A (would kill VIP owner path; previously untested with HA) | **75/75 OK** |
| worker-02 failure external availability | **failed** (0 ingress endpoints) | **75/75 OK** |
| app version / digest | 0.1.4 / `1cca2b59…872ff` | unchanged |

---

## 16. Limitations

- Tests used **kubelet stop**, not VMware VM power-off. Host network/kube-proxy on the failed node may still forward briefly under `externalTrafficPolicy=Cluster`.
- Soft topology spread (`ScheduleAnyway`) prefers spread but does not hard-guarantee it under all scheduling races.
- Observability had KSM gauges for ingress Deployment/pods; dedicated nginx ingress controller scrape metrics were not present (`up` for ingress job empty) and were not added in this milestone.
- Initial Argo sync hit a `ServerSideApply`+`Force` incompatibility on Argo CD v3.5.3; resolved by managing a full Deployment manifest without Force.
- Helm release still exists; HA desired state is Git/Argo. Keep `ingress-nginx-values.yaml` aligned before any manual `helm upgrade`.

---

## 17. Lessons Learned

1. Application HA ≠ external HA when the ingress data plane is a SPOF.  
2. Two ingress replicas on different workers fix the concrete outage mode seen in the prior lab.  
3. Soft topology spread matches lab recovery needs better than required anti-affinity.  
4. With `externalTrafficPolicy=Cluster`, surviving Ready ingress endpoints matter more than which speaker currently owns the VIP.  
5. GitOps ownership of HA fields (plus PDB) prevents silent drift back to replicas=1.

---

## 18. Future Networking Experiments

1. Full VM power-off vs kubelet stop — measure real ARP/MetalLB interrupt duration.  
2. `externalTrafficPolicy=Local` with MetalLB — study announce/endpoint co-location.  
3. Ingress controller metrics scrape (Prometheus ServiceMonitor) for request/error rates during failover.  
4. Three-worker spread / zone labels if the lab grows beyond two workers.
