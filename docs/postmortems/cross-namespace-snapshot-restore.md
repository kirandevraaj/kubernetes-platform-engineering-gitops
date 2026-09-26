# Postmortem: Cross-Namespace Snapshot Restore Failure

| Field | Value |
|---|---|
| Severity | SEV-3 (restore blocked) |
| Environment | AWS EBS CSI snapshots |

## Symptom
Cross-namespace VolumeSnapshot restore failed.

## Root cause
Restore/VSC binding constraints — resolved with **same-namespace static VolumeSnapshotContent** pattern used in lab.

## Detection
PVC Pending / snapshot restore errors; VolumeSnapshot* inspection.

## Fix
Same-namespace static VolumeSnapshotContent approach → restore succeeded (snapshot Ready ~72s; PVC→Running ~15s in lab timings — not SLA).

## Lesson
Do not imply this is the only possible cross-namespace failure mode; verify namespace and VSC objects early.
