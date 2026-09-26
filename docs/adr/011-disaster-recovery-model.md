# ADR 011: Disaster recovery model

- **Status:** Accepted

## Decision

DR model = **Git** (config) + **Terraform** (infra) + **EBS snapshots** (data) + **Docker Hub digests** (artifacts) + **runbooks** (people/process).

## Tested vs designed

| Item | Classification |
|---|---|
| Git/Argo recovery drills | Implemented + Verified (lab) |
| EBS snapshot restore | Implemented + Verified (lab timings) |
| Namespace / selfHeal timings | Verified |
| AWS Backup EKS restore | **Documented / Not tested** |
| Full EKS rebuild | **Not destructively tested** |
| Cross-region | **Not implemented** |

## Evidence

[disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) · [dr-lab-evidence.md](../dr-lab-evidence.md)
