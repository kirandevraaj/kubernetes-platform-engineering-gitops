# Documentation index

Master index for the Kubernetes Platform Engineering & GitOps Lab (Project 1).

**Start here:** [Portfolio](portfolio/README.md) · [Reference architecture](architecture/project1-reference-architecture.md) · [Operations](operations/README.md) · [ADRs](adr/README.md)

Classification: **Implemented + Verified** · **Partial** · **Documented / Designed** · **Not tested**

---

## Architecture

| Document | Path |
|---|---|
| Project 1 reference architecture | [architecture/project1-reference-architecture.md](architecture/project1-reference-architecture.md) |
| Platform version inventory | [architecture/platform-version-inventory.md](architecture/platform-version-inventory.md) |
| Ownership boundaries | [architecture/ownership-boundaries.md](architecture/ownership-boundaries.md) |
| Tool boundaries | [architecture/tool-boundaries.md](architecture/tool-boundaries.md) |
| Cost awareness | [architecture/cost-awareness.md](architecture/cost-awareness.md) |
| Final security review | [architecture/final-security-review.md](architecture/final-security-review.md) |
| Architecture overview (lab notes) | [architecture/architecture-overview.md](architecture/architecture-overview.md) |
| GitOps / CI/CD / networking / observability / reliability | [architecture/](architecture/) |

### Diagrams (portfolio)

| Diagram | Path |
|---|---|
| Reference architecture | [diagrams/project1-reference-architecture.svg](diagrams/project1-reference-architecture.svg) |
| Control vs data plane | [diagrams/project1-control-and-data-plane.svg](diagrams/project1-control-and-data-plane.svg) |
| Automation boundaries | [diagrams/project1-automation-boundaries.svg](diagrams/project1-automation-boundaries.svg) |
| Reliability stack | [diagrams/project1-reliability-stack.svg](diagrams/project1-reliability-stack.svg) |
| Security architecture | [diagrams/project1-security-architecture.svg](diagrams/project1-security-architecture.svg) |
| DR architecture | [diagrams/project1-dr-architecture.svg](diagrams/project1-dr-architecture.svg) |

---

## ADRs

[adr/README.md](adr/README.md) — Terraform, EKS, GitOps, digests, Kustomize, observability, ALB vs ingress, EBS CSI, RBAC, automation boundaries, DR model, ingress HA, local-path vs EBS.

---

## Foundation / GitOps / Observability / Security / Storage

| Topic | Authoritative |
|---|---|
| Argo advanced | [argo-advanced-patterns.md](argo-advanced-patterns.md) |
| Security / RBAC | [security-rbac.md](security-rbac.md) |
| AWS EBS storage | [aws-storage-statefulset.md](aws-storage-statefulset.md) · [aws-storage-resilience.md](aws-storage-resilience.md) |
| VMware storage | [vmware-storage-statefulset.md](vmware-storage-statefulset.md) |
| Networking anatomy | [vmware-networking-anatomy.md](vmware-networking-anatomy.md) |
| Observability | [architecture/observability.md](architecture/observability.md) |

---

## Automation

| Document | Path |
|---|---|
| Platform automation master guide | [automation/platform-automation-master-guide.md](automation/platform-automation-master-guide.md) |
| Interview notes | [automation-interview-notes.md](automation-interview-notes.md) |

---

## Disaster Recovery

| Document | Path |
|---|---|
| DR master guide | [disaster-recovery-master-guide.md](disaster-recovery-master-guide.md) |
| DR lab evidence | [dr-lab-evidence.md](dr-lab-evidence.md) |
| Runbook index | [runbooks/disaster-recovery-index.md](runbooks/disaster-recovery-index.md) |

---

## Operations

| Document | Path |
|---|---|
| Operations landing | [operations/README.md](operations/README.md) |
| Platform operations handbook | [operations/platform-operations-handbook.md](operations/platform-operations-handbook.md) |
| Interview notes | [operations/operations-interview-notes.md](operations/operations-interview-notes.md) |

---

## Runbooks · Checklists · Postmortems · Troubleshooting

| Area | Path |
|---|---|
| Runbooks | [runbooks/](runbooks/) |
| Checklists | [checklists/](checklists/) |
| Postmortems | [postmortems/](postmortems/) |
| Triage / matrix | [troubleshooting/triage-framework.md](troubleshooting/triage-framework.md) · [troubleshooting/troubleshooting-matrix.md](troubleshooting/troubleshooting-matrix.md) |

---

## Portfolio · Evidence · Interview

| Document | Path |
|---|---|
| Portfolio landing | [portfolio/README.md](portfolio/README.md) |
| Evidence index | [evidence/README.md](evidence/README.md) |
| Interview master guide | [project1-interview-master-guide.md](project1-interview-master-guide.md) |
| Timeline | [project-timeline.md](project-timeline.md) |
| Engineering journey | [project-engineering-journey.md](project-engineering-journey.md) |
| AWS obs degraded note | [portfolio/aws-observability-degraded-final-state.md](portfolio/aws-observability-degraded-final-state.md) |

---

## Design

| Document | Path |
|---|---|
| Environment strategy | [design/environment-strategy.md](design/environment-strategy.md) |
| Architecture decisions (early) | [design/architecture-decisions.md](design/architecture-decisions.md) |

Prefer numbered ADRs under [adr/](adr/) for decision rationale going forward.
