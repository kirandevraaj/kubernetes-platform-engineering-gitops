# PVC / PV Troubleshooting Runbook (Project 1 — Section 26)

**Scope:** PersistentVolumeClaim **Pending**, **Lost**, wrong binding, or pod **FailedMount**.  
**AWS lab anchor:** PVC `data-storage-demo-0`, PV bound to EBS `vol-05faa26874d720ecd`, AZ **ap-south-1b**, StorageClass `ebs-gp3`.  
**Related:** [`ebs-attach-troubleshooting.md`](./ebs-attach-troubleshooting.md), [`ebs-storage-recovery.md`](./ebs-storage-recovery.md).

---

## Symptoms

- PVC status **Pending** indefinitely.
- Pod events: `FailedMount`, `VolumeAttachment` errors, `Multi-Attach error`.
- PV **Released** / wrong claimRef.

## Impact

- StatefulSet ordinal stuck — no data path.
- Risk of data loss if PV deleted while bound — **DESTRUCTIVE**.

## Severity

**SEV-1** for production-like volume `vol-05faa26874d720ecd`; **SEV-3** for disposable `dr-storage-restore` PVCs.

## First 60 Seconds

1. **READ-ONLY:** `kubectl get pvc,pv -n storage-lab`
2. **READ-ONLY:** `kubectl describe pvc data-storage-demo-0 -n storage-lab`
3. **READ-ONLY:** `kubectl get volumeattachment`
4. **READ-ONLY:** Pod events for mount failures.

## Preconditions

- EBS CSI driver add-on healthy — **Design guidance**.
- Never delete lab production PVC/PV/volume during troubleshooting without DR approval.

## Evidence

```powershell
kubectl get pv pvc-612d84fb-dbd4-46d9-a17f-735216f0594d -o yaml
kubectl describe pod storage-demo-0 -n storage-lab
```

Record volume ID, AZ, node name (no AWS keys).

## Triage

| Condition | Cause |
|-----------|-------|
| PVC Pending, no PV | StorageClass, quota, CSI |
| Pod Pending, PVC Bound | AZ mismatch — volume in `ap-south-1b`, pod on `ap-south-1a` **Observed behavior** |
| Multi-Attach | Two pods same RWO volume |
| Released PV | Claim deleted — manual rebind risky |

## Diagnosis

1. **WaitForFirstConsumer** binding — pod must schedule first.
2. Cross-AZ: EBS regional to AZ — reschedule pod to **ap-south-1b** or snapshot restore to other AZ — [`ebs-snapshot-restore.md`](./ebs-snapshot-restore.md).
3. VMware: this lab’s primary block storage story is **AWS**; local PV issues **Design guidance** only unless hostPath lab added.

## Safe Remediation

| Action | Label |
|--------|-------|
| Read describe/events | READ-ONLY |
| Add node capacity same AZ | **WARNING — SAFE MUTATION** — scale MNG |
| Delete pod to remount same PVC | **WARNING — SAFE MUTATION** — StatefulSet ordinal |
| Delete PV/PVC/volume | **WARNING — DESTRUCTIVE** — dr-lab only |

Fix StorageClass or volumeMode in Git for new claims — not retroactive without migration.

## Verification

- PVC **Bound**; PV **Bound** correct claim.
- Pod **Running**; data file readable in mount path.

## Rollback

- Git revert storage manifest — does not restore deleted volumes.
- Snapshot restore path — [`ebs-snapshot-restore.md`](./ebs-snapshot-restore.md).

## Escalation

- CSI driver failure — [`aws-api-failure.md`](./aws-api-failure.md).
- Full volume loss — [`ebs-storage-recovery.md`](./ebs-storage-recovery.md).

## Do Not Do

- `kubectl delete pv` on production volume.
- Force-bind Released PV without understanding data ownership.

## Expected Recovery

| Case | RTO |
|------|-----|
| Pod remount same PVC | **~14s Observed** pod delete |
| AZ fix + reschedule | minutes |
| Attach after node loss | **~6.3 min Observed** |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Same-volume pod delete recovery | **Observed** |
| Cross-AZ Pending | **Observed** expected block |
| VMware PVC drills | **Not tested** in storage corpus |

## Postmortem Notes

- Volume ID, AZ, node, CSI events timeline.
- Whether Git or infra change caused SC mismatch.
