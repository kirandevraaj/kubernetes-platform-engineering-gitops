# Disaster Recovery Lab Evidence (Section 25)

Measured results from disposable DR drills. Not production SLOs.

## Lab targets vs observed

| Objective | LAB TARGET | OBSERVED |
|---|---|---|
| Configuration RPO | 0 committed changes (Git SoT) | Git revert restored desired ConfigMap (see Git drill) |
| Application recovery RTO | < 10 minutes | Git/Argo/namespace drills — see timings below |
| EBS snapshot recovery | measure actual | Snapshot ready ~72s; restore PVC→Running ~15s (after capacity available) |
| Node failure | prior ≈ 6.3 min | Prior milestone (`docs/aws-storage-resilience.md`) |
| Infrastructure rebuild | plan-only if safe | Terraform `plan -target=module.snapshot_controller`: 1 add; full destroy **not** tested |

---

## EBS CSI snapshot restore (AWS)

| Mark | UTC timestamp | Notes |
|---|---|---|
| Marker A written | 2026-09-26T12:10:49Z | Appended `SNAPSHOT-POINT-A` to `/data/state.txt` |
| Snapshot created | 2026-09-26T12:10:52Z | `VolumeSnapshot/storage-demo-snapshot` in `storage-lab` |
| Snapshot ReadyToUse | 2026-09-26T12:12:04Z | ~72 seconds |
| Snapshot handle | `snap-0d723d8cf105df54a` | EBS snapshot via CSI |
| Marker B written | 2026-09-26T12:12:06Z | Appended `SNAPSHOT-POINT-B` on **live** volume |
| Restore T0 (retry) | 2026-09-26T12:22:53Z | Same-namespace static VolumeSnapshot + PVC |
| PVC Bound | ~2026-09-26T12:23:01Z | |
| Pod Running / data verified | 2026-09-26T12:23:08Z | |

### Data verification

| Volume | Contents |
|---|---|
| Original `vol-05faa26874d720ecd` | Includes `SNAPSHOT-POINT-A` **and** `SNAPSHOT-POINT-B` |
| Restored `vol-059aed8064c33f116` | Includes `SNAPSHOT-POINT-A`; **does not** include `SNAPSHOT-POINT-B` |

Restored PV: `pvc-3617b24d-dfa7-4bce-892e-840208ba2154` · AZ `ap-south-1b` · gp3 · 1 GiB · **different** volume ID from original.

### RPO demonstrated (example window)

Elapsed snapshot-create → change-B ≈ **74 seconds**. Restore returned to snapshot point, not live state.

### Notes

- First restore attempt failed because PVC `dataSource` VolumeSnapshot must be **same namespace**; fixed with static `VolumeSnapshotContent` + VolumeSnapshot in `dr-storage-restore`.
- Temporary nodegroup scale to desiredSize=3 required (nodes were at 17/17 pods).

---

## CSI snapshot controller

| Item | Value |
|---|---|
| Add-on | `snapshot-controller` `v8.6.0-eksbuild.8` |
| VolumeSnapshotClass | `ebs-csi-snapclass` · driver `ebs.csi.aws.com` · deletionPolicy Delete |

---

## Git / Argo / namespace drills

Timings filled after VMware experiments in this file's update section below.
