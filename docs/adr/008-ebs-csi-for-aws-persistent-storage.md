# ADR 008: EBS CSI for AWS persistent storage

- **Status:** Accepted

## Decision

Use **EBS CSI** managed add-on with `ebs-gp3` StorageClass. PVC → PV → CSI → EBS volume.

## Topology

**EBS is AZ-scoped.** Worker failure recovery requires capacity in the same AZ (`ap-south-1b` for lab volume `vol-05faa26874d720ecd`). Observed worker/EBS recovery ~**6.3 minutes** (lab, not SLA).

## Evidence

[aws-storage-statefulset.md](../aws-storage-statefulset.md) · [aws-storage-resilience.md](../aws-storage-resilience.md) · [ebs-attach-troubleshooting.md](../runbooks/ebs-attach-troubleshooting.md) · [ebs-snapshot-restore.md](../runbooks/ebs-snapshot-restore.md)
