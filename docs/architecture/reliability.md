# Reliability & production hardening (local lab)

Status: local overlay adds HPA, PDB, explicit RollingUpdate, and soft topology spread for `platform-lab`. AWS overlay is unchanged.

## Architecture

```text
                    Argo CD (platform-lab-local)
                              |
                              v
                 kubernetes/overlays/local
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
   Deployment              HPA                 PDB
   replicas (Git=2)        min=2 max=4         minAvailable=1
   strategy:               CPU 70%             selector: platform-lab
     maxUnavailable: 0
     maxSurge: 1
   topologySpread:
     hostname, ScheduleAnyway
          |
          v
     Pods (prefer different workers)
          |
          +--> readiness (/health) --> Service endpoints
          +--> liveness  (/health) --> restart if stuck
```

| Concept | Who owns it | Meaning |
|---|---|---|
| **Deployment replicas (Git)** | Manifest baseline | Desired count when HPA is idle; Git keeps `2` as the floor. |
| **HPA desired replicas** | HorizontalPodAutoscaler | Runtime scale between 2 and 4 from CPU utilization vs request. |
| **PDB availability** | PodDisruptionBudget | During voluntary disruptions, keep at least one pod Available. |
| **Readiness** | Probe on `/health` | Pod receives Service traffic only when Ready. |
| **Liveness** | Probe on `/health` | Unhealthy process is restarted; not used for traffic gating. |

## HorizontalPodAutoscaler

| Field | Value |
|---|---|
| API | `autoscaling/v2` |
| Target | Deployment `platform-lab` |
| minReplicas | 2 |
| maxReplicas | 4 |
| Metric | CPU average utilization **70%** of request (`50m`) |

Argo CD Application `platform-lab-local` ignores `/spec/replicas` on the Deployment so HPA scaling does not fight Git sync.

### Lab limitation

Idle pods use ~2m CPU against a 50m request (~4% utilization). Sustained load that exceeds 70% of request may not be practical from the workstation without aggressive stress tools. The HPA object and metrics pipeline must still report successfully even when desired replicas stay at 2.

## PodDisruptionBudget

| Field | Value |
|---|---|
| API | `policy/v1` |
| minAvailable | 1 |
| Selector | `app.kubernetes.io/name=platform-lab`, `app.kubernetes.io/instance=platform-lab` |

Protects against draining both replicas during voluntary node/pod operations. Does not block involuntary failures (node crash).

## RollingUpdate

| Field | Value |
|---|---|
| type | RollingUpdate |
| maxUnavailable | 0 |
| maxSurge | 1 |

A new pod must become Ready before an old pod is terminated. Fits a 2-replica lab without dropping below one Available pod during the surge.

## Topology-aware placement

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
```

Prefers different Kubernetes nodes. `ScheduleAnyway` avoids Pending pods if only one worker is available.

## Probes

| Probe | Present | Path | Rationale |
|---|---|---|---|
| readiness | Yes | `/health` | Gate Service endpoints |
| liveness | Yes | `/health` | Restart hung processes |
| startup | **No** | — | FastAPI becomes ready in seconds; existing readiness `initialDelaySeconds: 3` is enough |

## Git layout (local only)

| Path | Role |
|---|---|
| `kubernetes/overlays/local/hpa.yaml` | HorizontalPodAutoscaler |
| `kubernetes/overlays/local/pdb.yaml` | PodDisruptionBudget |
| `kubernetes/overlays/local/deployment-reliability-patch.yaml` | strategy + topologySpreadConstraints |
| `gitops/projects/platform-lab.yaml` | Allow `HorizontalPodAutoscaler`, `PodDisruptionBudget` |
| `gitops/applications/platform-lab-local.yaml` | Ignore Deployment `/spec/replicas` |

## Validation commands

```powershell
kubectl --context=ckad-lab get deploy,hpa,pdb,pods -n platform-lab -o wide
kubectl --context=ckad-lab describe hpa -n platform-lab platform-lab
kubectl --context=ckad-lab describe pdb -n platform-lab platform-lab
kubectl --context=ckad-lab get rs -n platform-lab
curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/version
```

## Resilience tests (lab)

1. **Single pod delete.** Delete one Ready pod; Deployment recreates it; Service stays available; other pod should not restart unnecessarily.
2. **Rolling update.** Applying the reliability pod-template patch (or any template change) creates a new ReplicaSet with `maxUnavailable: 0` / `maxSurge: 1`.
3. **HPA.** Confirm `kubectl get hpa` shows TARGETS with a real CPU metric (not `<unknown>`). Scale-out may not occur under idle load; document that honestly.

## Observed validation (24 September 2026)

| Check | Result |
|---|---|
| Commit | `bc8181f` |
| Jenkins | Build `#16` SUCCESS; app CI stages skipped (no `app/**` change); no image build/push |
| Argo CD | `platform-lab-local` Synced/Healthy at `bc8181f` |
| Rolling update | Old RS `platform-lab-57bc9dcd78` → new RS `platform-lab-58697f7bf4` (pod-template reliability patch; same image `0.1.3`) |
| HPA | TARGETS `cpu: 4%/70%`; ScalingActive True; replicas stay at 2 under idle load |
| PDB | `minAvailable: 1`, Allowed disruptions: 1 |
| Pod delete | Deleted one pod; replacement Ready in ~13s; survivor restarts stayed 0; endpoints updated |
| Placement after recreate | Pods on `k8s-worker-01` and `k8s-worker-02` |
| App | `/health` healthy; `/version` `0.1.3` via `platform-lab.local` |

**Note:** Immediately after the RollingUpdate both new pods briefly landed on `k8s-worker-02` (`ScheduleAnyway` preference during surge). After deleting one pod, the replacement scheduled on `k8s-worker-01`, restoring spread.
