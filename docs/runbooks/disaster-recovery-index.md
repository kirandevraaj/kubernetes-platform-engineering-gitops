# Disaster Recovery Index (Project 1 — Section 26)

**Purpose:** Entry point for **catastrophic / rebuild-class** recovery — links **only** to Section 25 corpus and its runbooks.  
**Section 26** operational runbooks (pod, ingress, Git rollback, etc.) handle **day-2 incidents**; use this index when the question is **DR**, not a single failing Deployment.

**Honesty:** Items marked **Tested** in Section 25 have repo evidence; Section 26 files may be **Observed** or **Design guidance** separately.

---

## When to use Section 25 vs Section 26

| Question | Start here |
|----------|------------|
| One app unhealthy, rollout stuck, Argo OutOfSync | Section 26 runbooks in this directory (e.g. [`application-unhealthy.md`](./application-unhealthy.md), [`git-rollback.md`](./git-rollback.md)) |
| Namespace/app deleted, Git bad on `main`, EBS volume loss, EKS rebuild | **Section 25** below |
| Operator credential / GitHub / Terraform state loss | [`../business-continuity.md`](../business-continuity.md) |

---

## Section 25 — Master references

| Document | Description |
|----------|-------------|
| [Disaster Recovery Master Guide](../disaster-recovery-master-guide.md) | End-to-end DR reference |
| [DR Fundamentals](../disaster-recovery-fundamentals.md) | HA vs backup vs restore; RPO/RTO |
| [DR Baseline Inventory](../dr-baseline-inventory.md) | VMware + AWS read-only inventory |
| [Disaster Scenario Matrix](../disaster-scenario-matrix.md) | Tested vs documented scenarios |
| [DR Lab Evidence](../dr-lab-evidence.md) | Measured drill timings |
| [AWS Backup for EKS](../aws-backup-eks-dr.md) | AWS Backup scope |
| [Terraform DR](../terraform-dr.md) | Code vs state |
| [Terraform Recovery Runbook](../terraform-recovery-runbook.md) | Infrastructure rebuild sequence |
| [Business Continuity](../business-continuity.md) | People, DNS, dependencies |
| [DR Interview Notes](../disaster-recovery-interview-notes.md) | Q&A |

---

## Section 25 — Runbooks (do not duplicate here)

These files are **authoritative** for DR flows. Section 26 runbooks **cross-link** but do not replace them.

| Runbook | Path | Scope |
|---------|------|--------|
| AWS EKS Disaster Recovery | [`aws-eks-disaster-recovery.md`](./aws-eks-disaster-recovery.md) | EKS incident / rebuild flow |
| EBS Storage Recovery | [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) | Same-volume vs snapshot paths; `vol-05faa26874d720ecd` |
| Git and Argo CD Recovery | [`git-argo-recovery.md`](./git-argo-recovery.md) | Bad commit, App/namespace loss, GitHub outage |
| Terraform Infrastructure Recovery | [`terraform-infrastructure-recovery.md`](./terraform-infrastructure-recovery.md) | IaC rebuild |

**Automation failures (Section 25 adjacent):** [`ansible-failure.md`](./ansible-failure.md), [`python-automation.md`](./python-automation.md), [`automation-failure.md`](./automation-failure.md), [`aws-api-failure.md`](./aws-api-failure.md), [`kubernetes-api-failure.md`](./kubernetes-api-failure.md) — unchanged by Section 26.

---

## Section 25 — Diagrams

| Diagram | Path |
|---------|------|
| DR dependency graph | [`../diagrams/dr-dependency-graph.svg`](../diagrams/dr-dependency-graph.svg) |
| DR architecture | [`../diagrams/disaster-recovery-architecture.svg`](../diagrams/disaster-recovery-architecture.svg) |
| EKS recovery flow | [`../diagrams/eks-recovery-flow.svg`](../diagrams/eks-recovery-flow.svg) |
| EBS snapshot recovery | [`../diagrams/ebs-snapshot-recovery.svg`](../diagrams/ebs-snapshot-recovery.svg) |
| VMware vs AWS DR | [`../diagrams/vmware-vs-aws-dr.svg`](../diagrams/vmware-vs-aws-dr.svg) |

---

## Section 26 — Related operational runbooks (incident, not full DR)

Use for **partial failures**; escalate to Section 25 when data or control plane is lost.

| Topic | Runbook |
|-------|---------|
| Git revert / promotion mistake | [`git-rollback.md`](./git-rollback.md) |
| EBS attach delay | [`ebs-attach-troubleshooting.md`](./ebs-attach-troubleshooting.md) |
| Snapshot restore drill | [`ebs-snapshot-restore.md`](./ebs-snapshot-restore.md) |
| Worker node loss | [`worker-node-failure.md`](./worker-node-failure.md) |
| Argo sync / project errors | [`argo-sync-failure.md`](./argo-sync-failure.md), [`argocd-appproject-denied.md`](./argocd-appproject-denied.md) |

---

## Lab constants (quick reference)

| Item | Value |
|------|--------|
| Known-good digest | `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` (0.1.4) |
| VMware ingress VIP | `192.168.56.200` |
| AWS EBS lab volume | `vol-05faa26874d720ecd` · `ap-south-1b` |
| EBS attach recovery (node failure) | **~6.3 min Observed** |

---

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Section 25 DR drills (Git/Argo/namespace/snapshot) | **Observed** — see `dr-lab-evidence.md` |
| Full cluster destroy rebuild | **Documented only** |
| This index replaces Section 25 content | **No** — index only |

## Postmortem Notes

- Tag incidents **SEV** and **plane** (Git, Argo, K8s, AWS, VMware).
- Link Section 26 tactical runbook **and** Section 25 DR runbook if both used.
