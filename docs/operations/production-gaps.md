# Potential production enhancements (not lab requirements)

**Label:** **Design guidance** — not every production system needs every item on day one.

| Category | Gap vs Project 1 lab | Why it matters |
|---|---|---|
| Centralized alerting | Prometheus rules exist; paging immature | Wake humans for SEV-1 |
| Log aggregation | kubectl logs only | Correlation across pods |
| On-call / paging | Not tested | [escalation.md](./escalation.md) is role template only |
| Secret management | K8s Secrets; no Vault integration | Rotation, audit |
| Remote Terraform state | Local state **Observed** | Team concurrency, locking — [terraform-dr.md](../terraform-dr.md) |
| Backup retention policy | Ad-hoc snapshots | Compliance RPO |
| Multi-region DR | **Not tested** | Region loss |
| Registry redundancy | Docker Hub single | Pull failures block schedules |
| DNS failover | Lab hosts file / local DNS | Real user traffic |
| Certificate lifecycle | cert-manager patterns vary | Expiry outages |
| External synthetic monitoring | Manual curl | Blind spots outside cluster |
| SLOs / error budgets | Golden signals only | Prioritize engineering |
| Audit logging | Not comprehensive | Security investigations |
| Capacity planning | t3.medium 17-pod note | Surprise Pending |
| Cost governance | Lab size | FinOps |

---

## What Project 1 **does** provide

- GitOps desired state and rollback model  
- Dual-environment patterns (VMware + AWS)  
- Measured lab RTO/RPO samples — [rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md)  
- DR cross-links — [dr-lab-evidence.md](../dr-lab-evidence.md)  

---

## Related

- [operational-readiness-assessment.md](./operational-readiness-assessment.md)
- [business-continuity.md](../business-continuity.md)
