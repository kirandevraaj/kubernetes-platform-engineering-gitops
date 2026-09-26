# Escalation model

Escalate when **blast radius**, **duration**, **data/security impact**, or **unknown root cause** exceeds comfortable operator scope — prefer escalation over risky experimentation.

---

## Escalate when

| Trigger | Why |
|---|---|
| SEV-1 or SEV-2 > agreed duration | Time-boxed response failing |
| Suspected data loss on PVC/EBS | Wrong volume, AZ trap, delete |
| Security: unexpected cluster-admin, privileged pod, Secret exfil | [security-rbac.md](../security-rbac.md) |
| Git + Argo + Jenkins all impaired | Cannot restore desired state via normal path |
| Terraform state corruption suspected | [terraform-dr.md](../terraform-dr.md) |
| AWS API / EKS control plane errors | Outside kubectl-only fix |
| Recovery action requires **DESTRUCTIVE** step | Second pair of eyes |

---

## Escalation path (Design guidance — lab roles)

| Level | Role | Responsibility |
|---|---|---|
| L1 | Platform operator on shift | Triage, evidence, READ-ONLY, Git rollback |
| L2 | Platform engineer / owner | Infra (Terraform, EKS, VMware), Argo projects |
| L3 | Security / cloud account owner | IAM, breach, credential rotation |
| Vendor | AWS / VMware | Control plane, hardware |

**Not tested in Project 1:** Formal paging/on-call — see [production-gaps.md](./production-gaps.md).

---

## What to send upstream

Use [incident-evidence.md](./incident-evidence.md) minus secrets:

- Severity, impact, T0
- Context(s) affected
- Last known-good Git SHA / Argo revision
- What was **not** done yet (avoid duplicate destructive work)

---

## Stop conditions

Do **not** continue autonomous experimentation if:

- Each fix increases blast radius
- Root cause is unknown after structured triage ([triage-framework.md](../troubleshooting/triage-framework.md))
- Recovery requires `terraform destroy`, node drain at production scale, or manual EBS surgery

Related: [operational-antipatterns.md](./operational-antipatterns.md)
