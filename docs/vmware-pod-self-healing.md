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

## 17. Limitations

- Single delete on a 2-replica Deployment; not a full outage test.
- Prometheus replacement-UP timestamp is an upper bound from post-loop polling.
- Grafana may undersample a ~10s available-replica dip.
- Calico sandbox cleanup delayed victim removal from the API list.
- Not an HPA, Argo drift, rollout, or node-failure test.

---

## 18. Next Failure Experiment

Candidates for later milestones (separate):

- Node cordon/drain / node failure
- Multi-pod disruption vs PDB
- Bad image / CrashLoopBackOff recovery
- Readiness failure without delete
- AWS parity of the same single-pod heal

---

## Appendix — Commands used

```powershell
kubectl config current-context   # ckad-lab
kubectl get deploy,rs,pods,svc,endpoints,hpa,pdb -n platform-lab -o wide
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/version

# Intentional failure (exactly one pod):
kubectl delete pod platform-lab-9c5b867f-r455h -n platform-lab

kubectl get pods -n platform-lab -o wide
kubectl get deploy,endpoints -n platform-lab
kubectl get application platform-lab-local -n argocd
```
