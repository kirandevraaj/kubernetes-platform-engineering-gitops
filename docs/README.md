# Documentation index

Architecture, design, runbooks, and lab notes for the Kubernetes Platform Engineering & GitOps Lab.

## Operations (Section 26)

| Document | Path |
|---|---|
| Operations landing page | [operations/README.md](operations/README.md) |
| Platform Operations Handbook | [operations/platform-operations-handbook.md](operations/platform-operations-handbook.md) |
| Triage framework | [troubleshooting/triage-framework.md](troubleshooting/triage-framework.md) |
| Troubleshooting matrix | [troubleshooting/troubleshooting-matrix.md](troubleshooting/troubleshooting-matrix.md) |
| Daily health checklist | [checklists/daily-platform-health.md](checklists/daily-platform-health.md) |
| Postmortems | [postmortems/](postmortems/) |
| Operations interview notes | [operations/operations-interview-notes.md](operations/operations-interview-notes.md) |

Concept → architecture → experiment → runbook → recovery: start at [operations/README.md](operations/README.md).

## Disaster Recovery (Section 25)

| Document | Description |
|---|---|
| [Disaster Recovery Master Guide](disaster-recovery-master-guide.md) | End-to-end DR reference (concepts → production → interview) |
| [DR Fundamentals](disaster-recovery-fundamentals.md) | HA vs backup vs restore vs DR; RPO/RTO; what each plane protects |
| [DR Baseline Inventory](dr-baseline-inventory.md) | Read-only inventory of VMware + AWS at Section 25 start |
| [Disaster Scenario Matrix](disaster-scenario-matrix.md) | Failure scenarios, recovery sources, tested vs documented |
| [AWS Backup for EKS](aws-backup-eks-dr.md) | AWS Backup scope, prerequisites, limitations |
| [Terraform DR](terraform-dr.md) | Code vs state; local state risks; backup model |
| [Terraform Recovery Runbook](terraform-recovery-runbook.md) | Conceptual infrastructure rebuild sequence |
| [Business Continuity](business-continuity.md) | People, credentials, DNS, deps beyond Kubernetes |
| [DR Interview Notes](disaster-recovery-interview-notes.md) | Concise interview Q&A grounded in this lab |

### DR runbooks

| Runbook | Path |
|---|---|
| AWS EKS Disaster Recovery | [runbooks/aws-eks-disaster-recovery.md](runbooks/aws-eks-disaster-recovery.md) |
| EBS Storage Recovery | [runbooks/ebs-storage-recovery.md](runbooks/ebs-storage-recovery.md) |
| Git / Argo Recovery | [runbooks/git-argo-recovery.md](runbooks/git-argo-recovery.md) |
| Terraform Infrastructure Recovery | [runbooks/terraform-infrastructure-recovery.md](runbooks/terraform-infrastructure-recovery.md) |

### DR diagrams

| Diagram | Path |
|---|---|
| DR dependency graph | [diagrams/dr-dependency-graph.svg](diagrams/dr-dependency-graph.svg) |
| DR architecture | [diagrams/disaster-recovery-architecture.svg](diagrams/disaster-recovery-architecture.svg) |
| EKS recovery flow | [diagrams/eks-recovery-flow.svg](diagrams/eks-recovery-flow.svg) |
| EBS snapshot recovery | [diagrams/ebs-snapshot-recovery.svg](diagrams/ebs-snapshot-recovery.svg) |
| VMware vs AWS DR | [diagrams/vmware-vs-aws-dr.svg](diagrams/vmware-vs-aws-dr.svg) |

## Architecture

| Document | Path |
|---|---|
| Architecture overview | [architecture/architecture-overview.md](architecture/architecture-overview.md) |
| GitOps flow | [architecture/gitops-flow.md](architecture/gitops-flow.md) |
| CI/CD flow | [architecture/ci-cd-flow.md](architecture/ci-cd-flow.md) |
| Networking | [architecture/networking.md](architecture/networking.md) |
| Observability | [architecture/observability.md](architecture/observability.md) |
| Reliability | [architecture/reliability.md](architecture/reliability.md) |
| Argo GitOps reference | [architecture/argo-gitops-reference.md](architecture/argo-gitops-reference.md) |

## Design

| Document | Path |
|---|---|
| Environment strategy | [design/environment-strategy.md](design/environment-strategy.md) |
| Architecture decisions | [design/architecture-decisions.md](design/architecture-decisions.md) |

## Platform labs (selected)

| Topic | Path |
|---|---|
| Security / RBAC | [security-rbac.md](security-rbac.md) |
| AWS EBS StatefulSet | [aws-storage-statefulset.md](aws-storage-statefulset.md) |
| AWS storage resilience | [aws-storage-resilience.md](aws-storage-resilience.md) |
| Argo advanced patterns | [argo-advanced-patterns.md](argo-advanced-patterns.md) |
| Platform automation master guide | [automation/platform-automation-master-guide.md](automation/platform-automation-master-guide.md) |
| Toolchain inventory | [toolchain-inventory.md](toolchain-inventory.md) |

## Operations (Section 26)

| Document | Description |
|---|---|
| Operations index | [operations/README.md](operations/README.md) |
| Platform Operations Handbook | [operations/platform-operations-handbook.md](operations/platform-operations-handbook.md) |
| Platform inventory | [operations/platform-inventory.md](operations/platform-inventory.md) |
| Golden signals | [operations/golden-signals.md](operations/golden-signals.md) |
| Triage framework | [troubleshooting/triage-framework.md](troubleshooting/triage-framework.md) |
| Troubleshooting matrix | [troubleshooting/troubleshooting-matrix.md](troubleshooting/troubleshooting-matrix.md) |
| Runbook template | [runbooks/runbook-template.md](runbooks/runbook-template.md) |
| Daily / shift checklists | [checklists/daily-platform-health.md](checklists/daily-platform-health.md) |

DR operational timings link [operations/rpo-rto-operational-guide.md](operations/rpo-rto-operational-guide.md) to Section 25 [dr-lab-evidence.md](dr-lab-evidence.md) (authoritative drill detail).

## Troubleshooting

| Document | Path |
|---|---|
| Common issues | [troubleshooting/common-issues.md](troubleshooting/common-issues.md) |
| Triage framework | [troubleshooting/triage-framework.md](troubleshooting/triage-framework.md) |
| Troubleshooting matrix | [troubleshooting/troubleshooting-matrix.md](troubleshooting/troubleshooting-matrix.md) |
