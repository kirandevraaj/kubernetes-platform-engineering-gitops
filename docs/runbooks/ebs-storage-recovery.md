# EBS Storage Recovery Runbook (Project 1 — Section 25)

**Scope:** AWS EKS storage lab — namespace `storage-lab`, StatefulSet `storage-demo`, PVC `data-storage-demo-0`, PV `pvc-612d84fb-dbd4-46d9-a17f-735216f0594d`, EBS `vol-05faa26874d720ecd`, StorageClass `ebs-gp3`, AZ `ap-south-1b`.  
**Disposable restore namespace:** `dr-storage-restore` only for snapshot-to-new-volume drills.  
**Never delete** the original volume, PVC, PV, or `storage-demo` workload during exercises.

---

## Concepts

| Term | In this lab |
|------|-------------|
| **Same-volume recovery** | Pod or node failure; **same** EBS volume reattached via CSI |
| **Snapshot-to-new-volume recovery** | New EBS volume from snapshot; **new** PVC/PV; proves point-in-time RPO |
| **EBS volume** | AZ-scoped block device (`ap-south-1b`) |
| **EBS snapshot** | Regional point-in-time artifact used to create new volumes (possibly in another AZ in the same region) |

CSI snapshot CRDs were **not** present at Section 25 inventory; install snapshot controller add-on before VolumeSnapshot workflow (**TBD**).

---

## Decision: Same-Volume vs Snapshot Restore

```text
Is vol-05faa26874d720ecd (or target PVC) still intact and Bound?
  YES → Same-volume path (Section A)
  NO  → Snapshot / AWS Backup path (Section B) — requires prior backup
```

| Path | When to use | RPO | Test status |
|------|-------------|-----|-------------|
| **A. Same-volume** | Pod delete, worker replace in **same AZ** | No snapshot needed; live data | **Tested** ([`aws-storage-statefulset.md`](../aws-storage-statefulset.md), [`aws-storage-resilience.md`](../aws-storage-resilience.md)) |
| **B. Snapshot → new volume** | Overwrite, volume loss, copy for forensics, AZ escape with restore | Last Ready snapshot | **Documented only** until Section 25 Phases 19–27 complete |

---

## Section A — Same-Volume Recovery

### A.1 Pod deleted

1. Confirm PVC still **Bound:** `kubectl -n storage-lab get pvc data-storage-demo-0`
2. Delete pod only if intentional test: `kubectl delete pod storage-demo-0 -n storage-lab`
3. Wait for StatefulSet to recreate ordinal `0`.
4. Verify EBS unchanged: volume ID `vol-05faa26874d720ecd`.
5. Verify data: exec into pod, `cat /data/state.txt` (content per lab baseline).

**Observed:** ~**14 seconds** to Ready after pod delete.

### A.2 Worker node failure (same AZ)

1. Ensure **at least one Ready worker in `ap-south-1b`** (lab used temporary node group `storage-resilience-test-1b` during experiment).
2. Terminate failed instance or let MNG replace node — **only** in controlled exercises.
3. Watch pod: Pending → ContainerCreating → Running; CSI **AttachVolume** events.
4. Do **not** manually `aws ec2 attach-volume` — EBS CSI owns attach/detach.

**Observed:** **≈ 6.3 minutes** T0 (node terminate) → pod Ready ([`aws-storage-resilience.md`](../aws-storage-resilience.md)).

### A.3 Cross-AZ scheduling failure (not a recovery — expected block)

If pod schedules to `ap-south-1a` while volume is in `ap-south-1b`, pod stays Pending. **Recovery:** reschedule to same AZ or use snapshot restore to create volume in target AZ (Section B).

---

## Section B — Snapshot-to-New-Volume Recovery

Use **`dr-storage-restore`** namespace; do not rebind to existing PV.

### B.1 Prerequisites

- EBS CSI driver add-on healthy (`aws-ebs-csi-driver`).
- Snapshot controller + `VolumeSnapshotClass` for `ebs.csi.aws.com` (**TBD** install via Terraform).
- Prior **VolumeSnapshot** of `data-storage-demo-0` in Ready state (**TBD**).

### B.2 Create snapshot (production volume — non-destructive)

On live `storage-demo-0` (exercise markers):

1. Write marker `SNAPSHOT-POINT-A` to `/data/state.txt`; fsync.
2. Create `VolumeSnapshot` (e.g. `storage-demo-snapshot`) referencing PVC `data-storage-demo-0`.
3. Wait `ReadyToUse=true`; record `snapshotHandle`, creation time.
4. Write `SNAPSHOT-POINT-B` on **live** volume after snapshot ready (proves point-in-time).

Original PVC/PV/volume remain in use.

### B.3 Restore PVC from snapshot

1. Create namespace `dr-storage-restore` (if not exists).
2. Create PVC `restored-storage` with:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-storage
  namespace: dr-storage-restore
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 1Gi
  dataSource:
    name: storage-demo-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

3. Wait **Bound**; note **new** PV and **new** EBS volume ID (must differ from `vol-05faa26874d720ecd`).
4. Deploy pod/StatefulSet `storage-restore-demo` mounting `/data`.

### B.4 Verify restored data

- `cat /data/state.txt` should contain **SNAPSHOT-POINT-A** and **not** `SNAPSHOT-POINT-B` if B was written after snapshot.
- Record T0–T5 timings for RTO (PVC create → Bound → Pod Ready → data verified).

If behavior differs, **stop** and document actual contents — do not alter data to pass the test.

### B.5 Cleanup (disposable only)

After documentation:

- Delete restore pod, PVC, PV (if reclaim allows), VolumeSnapshot, and **restored** EBS volume/snapshot.
- **Do not** delete original `vol-05faa26874d720ecd` or `data-storage-demo-0`.

---

## Object Relationships (reference)

```text
StatefulSet storage-demo
  └── Pod storage-demo-0
        └── volumeMount /data
              └── PVC data-storage-demo-0
                    └── PV pvc-612d84fb-dbd4-46d9-a17f-735216f0594d
                          └── EBS vol-05faa26874d720ecd (gp3, ap-south-1b)

Snapshot path (isolated):
  VolumeSnapshot storage-demo-snapshot
        └── EBS snapshot (AWS)
              └── new PV/PVC restored-storage
                    └── new EBS volume (new ID)
                          └── Pod storage-restore-demo
```

---

## VolumeSnapshot / PVC / PV / StatefulSet Workflow Summary

| Step | Kubernetes object | AWS artifact |
|------|-------------------|--------------|
| 1 | `VolumeSnapshotClass` | — |
| 2 | `VolumeSnapshot` → source PVC | EBS snapshot created by CSI |
| 3 | PVC with `dataSource` | New EBS volume from snapshot |
| 4 | Dynamic PV bound to PVC | Volume in selected AZ |
| 5 | Pod/StatefulSet mount | Attach via CSI |

For **same-volume** path, skip steps 1–4; StatefulSet keeps PVC template binding to existing claim.

---

## Failure Modes

| Issue | Likely cause | Action |
|-------|--------------|--------|
| PVC Pending | No snapshot controller / wrong SC | Install add-on; check `VolumeSnapshot` status |
| Pod Pending (AZ) | Volume AZ ≠ node AZ | Schedule to correct AZ or restore snapshot in target AZ |
| Wrong data after restore | Restored wrong snapshot or live mount | Compare volume IDs; verify snapshot time |
| Original volume at risk | Accidental delete | IAM deny delete; do not run cleanup on `storage-lab` |

---

## Related

- Diagram: [`../diagrams/ebs-snapshot-recovery.svg`](../diagrams/ebs-snapshot-recovery.svg)
- [`../aws-storage-statefulset.md`](../aws-storage-statefulset.md)
- [`../aws-storage-resilience.md`](../aws-storage-resilience.md)
- [`aws-eks-disaster-recovery.md`](./aws-eks-disaster-recovery.md)
