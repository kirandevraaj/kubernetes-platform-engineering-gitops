# Pod Failure Runbook (Project 1 — Section 26)

**Scope:** Pod **Failed**, **CrashLoopBackOff**, **Error**, or **Evicted** — not merely NotReady.  
**Namespaces:** `platform-lab`, `storage-lab`, advanced lab namespaces as applicable.  
**Related:** [`pod-not-ready.md`](./pod-not-ready.md), [`worker-node-failure.md`](./worker-node-failure.md), [`pvc-pv-troubleshooting.md`](./pvc-pv-troubleshooting.md).

---

## Symptoms

- `kubectl get pods` shows restarts climbing, `CrashLoopBackOff`, or `Error`.
- Events: `Failed`, `BackOff`, `FailedMount`, `FailedAttachVolume`.
- ReplicaSet may still meet desired count if replacements succeed elsewhere.

## Impact

- Reduced capacity if multiple pods fail; **single pod delete** on 2-replica Deployment often **no user impact** (lab).
- StatefulSet ordinal 0 failure blocks writes for that workload.
- Crash loops increase log/metrics noise and pull pressure.

## Severity

| Pattern | Severity |
|---------|----------|
| One pod of N≥2, others Ready | **SEV-3** |
| All app pods failing | **SEV-2** |
| Storage mount/attach failure on prod volume | **SEV-1** — protect data first |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get pods -n <ns> -o wide`
2. **READ-ONLY:** `kubectl describe pod <name> -n <ns>` — Last State, Events
3. **READ-ONLY:** `kubectl logs <pod> -n <ns> --previous` (if restarted)
4. Check node: `kubectl get node <node>` — Ready?

## Preconditions

- Confirm namespace is disposable vs production-like before any delete.
- AWS EBS workload: note PVC/PV/volume ID before node or pod actions — [`ebs-storage-recovery.md`](./ebs-storage-recovery.md).

## Evidence

```powershell
kubectl get pod <pod> -n <ns> -o yaml
kubectl get events -n <ns> --field-selector involvedObject.name=<pod>
kubectl get rs -n <ns> -l app.kubernetes.io/name=platform-lab
```

Capture exit code, OOMKilled, image pull errors (no secret values in tickets).

## Triage

| Event / state | Direction |
|---------------|-----------|
| `ImagePullBackOff` | Registry/tag/digest; Git overlay pin |
| `OOMKilled` | Limits; memory leak |
| `FailedMount` / CSI | [`pvc-pv-troubleshooting.md`](./pvc-pv-troubleshooting.md) |
| Node NotReady | [`worker-node-failure.md`](./worker-node-failure.md) |
| Probe-only failures | [`pod-not-ready.md`](./pod-not-ready.md) |

## Diagnosis

1. **Container exit:** logs + `terminated.reason`.
2. **Scheduling:** affinity, taints, resource requests vs node capacity (lab: t3.medium **17 pod** ceiling observed during DR drill — [`dr-lab-evidence.md`](../dr-lab-evidence.md)).
3. **GitOps:** confirm Deployment template matches intended digest — do not patch image live on platform apps.

## Safe Remediation

| Action | Label |
|--------|-------|
| Read logs/events | READ-ONLY |
| Fix root cause in Git; Argo sync | **SAFE MUTATION** (preferred) |
| Delete single failed pod to recreate | **WARNING — SAFE MUTATION** — OK for Deployment; StatefulSet ordinal needs care |
| Delete PVC/PV/volume | **WARNING — DESTRUCTIVE** — never on `vol-05faa26874d720ecd` without DR plan |

**Observed (Project 1):** Pod delete on Deployment replaced pod in **~10s** (VMware platform-lab resilience docs).

## Verification

- New pod **Running** and **Ready** (if probes pass).
- Service Endpoints include pod IP.
- For storage: data marker file unchanged on same-volume path.

## Rollback

- App config: **Git revert** → Argo — [`git-rollback.md`](./git-rollback.md).
- Not primary: `kubectl rollout undo`.

## Escalation

- Repeated crashes after good digest: application owner.
- CSI attach stuck >10m AWS: [`ebs-attach-troubleshooting.md`](./ebs-attach-troubleshooting.md).

## Do Not Do

- `kubectl delete pod --force --grace-period=0` on StatefulSet without understanding volume detach.
- Scale Deployment to 0 on production-like apps without change approval.
- Commit Secrets to Git as “fix”.

## Expected Recovery

| Cause | Recovery |
|-------|----------|
| Transient node/kubelet | Self-heal after node Ready |
| Bad release | Git rollback + rollout |
| EBS reattach after node loss | **~6.3 min** attach recovery **Observed** (AWS lab) |

## Observed Project 1 Result

| Scenario | Result |
|----------|--------|
| Deployment pod delete replace | **Observed** ~10s VMware |
| StatefulSet pod + same EBS volume | **Observed** ~14s Ready after delete |
| Node terminate + volume reattach | **Observed** ~6.3 min |

## Postmortem Notes

- Was failure isolated to one cluster overlay (local vs aws)?
- Did HPA/PDB affect replacement timing?
- Attach timeline if storage involved.
