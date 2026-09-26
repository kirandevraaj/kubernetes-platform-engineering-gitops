# EBS Attach Troubleshooting Runbook (Project 1 — Section 26)

**Scope:** AWS EBS volume attach/detach stuck — CSI **VolumeAttachment**, pod **ContainerCreating** / **FailedAttachVolume**.  
**Lab volume:** `vol-05faa26874d720ecd` · AZ **ap-south-1b** · attach recovery **~6.3 min** after worker failure **Observed**.

---

## Symptoms

- Pod stuck **ContainerCreating** with mount/attach events.
- `VolumeAttachment` not **Attached** or stuck **Detached** loop.
- AWS EC2 volume state **in-use** on wrong instance or **available** but not mounted.

## Impact

- Stateful workload offline until attach completes.
- Long attach windows exceed Deployment-style **~10s** expectations.

## Severity

**SEV-2** for `storage-demo-0`; **SEV-1** if data corruption suspected — stop writes.

## First 60 Seconds

1. **READ-ONLY:** `kubectl describe pod storage-demo-0 -n storage-lab`
2. **READ-ONLY:** `kubectl get volumeattachment`
3. **READ-ONLY:** `kubectl get nodes -L topology.kubernetes.io/zone`
4. **READ-ONLY:** PVC → PV → volumeHandle / volume ID mapping.

## Preconditions

- Do **not** manually attach EBS in EC2 console — EBS CSI owns lifecycle **Design guidance**.
- Pod must schedule in **same AZ** as volume.

## Evidence

```powershell
kubectl get events -n storage-lab --sort-by='.lastTimestamp'
kubectl get pv -o custom-columns=NAME:.metadata.name,VOLUME:.spec.csi.volumeHandle,AZ:.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]
```

AWS CLI READ-ONLY (use instance/volume IDs from describe output):

```powershell
aws ec2 describe-volumes --volume-ids vol-05faa26874d720ecd
aws ec2 describe-volume-status --volume-ids vol-05faa26874d720ecd
```

## Triage

| Signal | Action |
|--------|--------|
| Node NotReady | [`worker-node-failure.md`](./worker-node-failure.md) |
| AZ mismatch | Reschedule to `ap-south-1b` |
| CSI node daemon issue | Restart **WARNING — SAFE MUTATION** node plugin pod — lab only |
| 17 pods/node cap | Scale node group — **Observed** DR drill |

## Diagnosis

1. **Observed timeline:** T0 node terminate → pod Ready **≈ 6.3 minutes** with **same** volume ID intact.
2. Stuck attachment after hard terminate may need controller retry — wait before manual intervention.
3. Multi-Attach: second pod on RWO — scale down duplicate StatefulSet/replica misuse.

## Safe Remediation

1. **READ-ONLY wait** through CSI retry window (lab: up to ~10m **Design guidance**).
2. **WARNING — SAFE MUTATION:** Cordon bad node; delete pod to trigger reschedule on healthy node same AZ.
3. **WARNING — SAFE MUTATION:** Increase MNG desired size in **ap-south-1b** for capacity — Observed during snapshot drill.
4. **DESTRUCTIVE:** Force-detach volume in AWS — **last resort**, risks corruption — **Not tested**; escalate.

## Verification

- Pod **Running**; mount readable.
- Volume **in-use** on correct node ID.
- Original data markers present (`state.txt`).

## Rollback

- N/A for attach — forward fix. If wrong volume attached, restore from snapshot — [`ebs-snapshot-restore.md`](./ebs-snapshot-restore.md).

## Escalation

- [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) Section A/B.
- AWS support if volume stuck **busy** **Design guidance**.

## Do Not Do

- Delete `vol-05faa26874d720ecd`.
- Attach volume to two nodes simultaneously.
- `kubectl rollout undo` for storage — irrelevant; use Git for manifest fixes only.

## Expected Recovery

**Observed ~6.3 min** node failure path; faster for simple pod delete remount **~14s**.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| ~6.3 min attach after node terminate | **Observed** |
| Manual EC2 attach | **Not tested** — avoid |
| Pod density blocking schedule | **Observed** DR evidence |

## Postmortem Notes

- Attach start/end UTC; node instance IDs.
- Whether capacity or CSI caused delay.
