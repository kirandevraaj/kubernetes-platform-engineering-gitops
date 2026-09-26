# ADR 013: local-path vs EBS storage

- **Status:** Accepted

## Decision

| Environment | Storage | Persistence model |
|---|---|---|
| VMware | `local-path` | Node-local lab persistence |
| AWS | EBS CSI `ebs-gp3` | AZ-scoped block volume |

## Rationale

Match environment constraints: simple local lab vs cloud block storage with CSI/snapshots. Do not treat local-path as production HA storage.

## Evidence

[vmware-storage-statefulset.md](../vmware-storage-statefulset.md) · [aws-storage-statefulset.md](../aws-storage-statefulset.md)
