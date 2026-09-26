# EBS Snapshot Restore Runbook (Project 1 — Section 26)

**Scope:** Restore data from **VolumeSnapshot** to a **new** PVC/PV/volume — disposable namespace `dr-storage-restore`.  
**Cross-namespace lesson:** PVC `dataSource` VolumeSnapshot must be **same namespace** as PVC — first restore failed; fixed with static **VolumeSnapshotContent** **Observed** [`dr-lab-evidence.md`](../dr-lab-evidence.md).  
**Deep recovery:** [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) (Section 25 — do not overwrite).

---

## Symptoms

- Restore PVC **Pending** — `dataSource` reference invalid.
- Error: snapshot in namespace X, PVC in namespace Y.
- Snapshot **ReadyToUse=false** or content binding missing.

## Impact

- RPO window defined by last Ready snapshot — demo **~72s** snapshot ready **Observed**.
- Wrong restore path could bind to wrong PV — data leak risk across tenants **Design guidance**.

## Severity

**SEV-2** during drill; **SEV-1** if attempting restore over live `storage-lab` volume.

## First 60 Seconds

1. **READ-ONLY:** `kubectl get volumesnapshot,volumesnapshotcontent`
2. **READ-ONLY:** Confirm target namespace is **`dr-storage-restore`** not `storage-lab`.
3. **READ-ONLY:** Snapshot `ReadyToUse` and `snapshotHandle` (e.g. `snap-0d723d8cf105df54a` in lab evidence — example ID only).

## Preconditions

- Snapshot controller add-on **`snapshot-controller` v8.6.0-eksbuild.8** **Observed** installed.
- `VolumeSnapshotClass` `ebs-csi-snapclass` driver `ebs.csi.aws.com`.
- **Never** rebind restore to `vol-05faa26874d720ecd` production PVC.

## Evidence

Timings from [`dr-lab-evidence.md`](../dr-lab-evidence.md):

| Mark | OBSERVED |
|------|----------|
| Snapshot ReadyToUse | ~72s |
| Restore PVC Bound → Pod Running | ~15s after capacity fix |
| RPO demo A present, B absent on restored vol | **Observed** |

## Triage

| Failure | Fix |
|---------|-----|
| Cross-namespace snapshot ref | Same-namespace VolumeSnapshot + static VolumeSnapshotContent |
| No node in AZ | Scale MNG **ap-south-1b** |
| Snapshot not ready | Wait or recreate snapshot READ-ONLY wait |

## Diagnosis

### Cross-namespace issue **Observed**

First attempt: PVC in `dr-storage-restore` referencing snapshot CR in `storage-lab` — **failed**.

**Fix pattern (lab-tested):**

1. Create static `VolumeSnapshotContent` pointing at EBS snapshot handle.
2. Create namespaced `VolumeSnapshot` in **`dr-storage-restore`** with `volumeSnapshotContentName`.
3. Create PVC with `dataSource.name` matching that VolumeSnapshot **in same namespace**.

**Design guidance:** Prefer snapshot and restore entirely in one disposable namespace for clarity.

## Safe Remediation

1. Write marker **SNAPSHOT-POINT-A** before snapshot — exercise only (**WARNING — SAFE MUTATION** on disposable data).
2. Create VolumeSnapshot from live PVC — **WARNING — SAFE MUTATION** — non-destructive to source if read-only snap.
3. Apply restore manifests in `dr-storage-restore` via Git or kubectl — **WARNING — SAFE MUTATION**.
4. Verify pod reads **A** not **B** after point-in-time restore.

## Verification

- Restored volume **different** ID (`vol-059aed8064c33f116` example in evidence).
- Pod Running; `cat /data/state.txt` matches snapshot point.
- Original volume unchanged still has A+B.

## Rollback

- Delete disposable restore namespace resources (**WARNING — DESTRUCTIVE** — dr-storage-restore only).
- Git revert restore manifests — [`git-rollback.md`](./git-rollback.md).

## Escalation

- Section 25 [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) Section B.
- Snapshot controller CRD missing — install add-on.

## Do Not Do

- Restore over production PVC `data-storage-demo-0` without maintenance window.
- Paste AWS credentials in docs.
- Assume cross-namespace snapshot refs work.

## Expected Recovery

**Observed:** Ready snapshot ~72s; restore pod ~15s once AZ/capacity OK.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Cross-ns restore failure | **Observed** |
| Static VolumeSnapshotContent fix | **Observed** |
| Full region DR | **Not tested** |

## Postmortem Notes

- Document namespace of snapshot vs PVC.
- Record snapshot handle and restored volume ID for cost cleanup (delete disposable snap/vol).
