# Operational readiness assessment (Project 1)

Qualitative status — **no scoring/ranking**. Use for gap conversations before calling the lab “production-ready.”

| Capability | Status | Notes |
|---|---|---|
| **Observability** | Partially implemented | Prometheus/Grafana/KSM; centralized alerting **Design guidance** |
| **Automation** | Partially implemented | Python doctor/verify; ops health/evidence **may** be extended — see mission Phase 77 |
| **Recovery** | Partially implemented | Git/Argo/namespace/EBS snapshot **Observed**; full EKS rebuild **documented only** |
| **Security** | Partially implemented | RBAC/PSA/**Observed** NP split — [security-rbac.md](../security-rbac.md) |
| **Documentation** | Implemented | Architecture + DR + Section 26 ops corpus |
| **Change control** | Implemented | Git + Jenkins + Argo; anti-patterns documented |
| **Backup** | Partially implemented | EBS snapshots **Observed**; AWS Backup EKS **not executed** |
| **DR** | Partially implemented | [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) |
| **Runbooks** | Implemented | Section 26 runbook set + template |
| **Testing** | Partially implemented | Lab experiments; no continuous game days **Design guidance** |

---

## Environment readiness snapshot

| Environment | Strength | Gap |
|---|---|---|
| VMware `ckad-lab` | Full stack for GitOps, ingress HA, Calico NP | Single-host lab; no multi-region |
| AWS EKS | Real ALB/EBS/CSI | NP not enforcing; small nodes; local Terraform state |

---

## Before declaring “ready for prod”

Review [production-gaps.md](./production-gaps.md) and [observed-vs-untested.md](./observed-vs-untested.md).

---

## Related

- [platform-operations-handbook.md](./platform-operations-handbook.md) §32
- [dr-baseline-inventory.md](../dr-baseline-inventory.md)
