# Platform Operations Handbook

**Project:** Kubernetes Platform Engineering & GitOps Lab — Section 26  
**Audience:** Operators responding at 2 AM  
**Rule:** Prefer **Observed in Project 1** facts. Label theory as **Design guidance** or **Not tested in Project 1**.

**Landing page:** [README.md](./README.md)  
**Diagrams:** [platform-operating-model.svg](../diagrams/platform-operating-model.svg) · [platform-failure-domain.svg](../diagrams/platform-failure-domain.svg) · [platform-operations-lifecycle.svg](../diagrams/platform-operations-lifecycle.svg)

---

## 1. Purpose

This handbook converts Project 1 experiments into a usable **Platform Operations** system: how to observe, triage, remediate safely, verify, and learn — without inventing untested behavior.

At 2 AM the questions are:

1. What do I check first?
2. What next?
3. What actions are safe?
4. How do I know it is fixed?
5. What evidence do I preserve?

## 2. Platform Scope

| In scope | Out of scope (this milestone) |
|---|---|
| VMware `ckad-lab` + AWS `platform-lab-aws` | New destructive failure drills |
| App `platform-lab` `0.1.4` | Changing application image/digest |
| Argo Applications (per-cluster) | Global Argo config mutation |
| Storage demos (local-path / EBS) | Manual EBS attach/detach |
| Observability, security-lab, automation CLI | Blind Terraform destroy |

## 3. Environment Overview

| | VMware | AWS |
|---|---|---|
| Context | `ckad-lab` | `platform-lab-aws` |
| Kubernetes | **1.31.14** | **1.36.4** (EKS) |
| Nodes | 3 Ready | 2 × t3.medium |
| Region / VIP | MetalLB `192.168.56.200` | `ap-south-1` ALB |
| Storage | `local-path` | `ebs-gp3` / `vol-05faa26874d720ecd` |
| Argo CD | **v3.5.3** | **v3.1.0** |

Treat Argo control planes as **separate**. Details: [platform-inventory.md](./platform-inventory.md).

## 4. VMware Environment

- Control plane + workers on VMs; CNI Calico; MetalLB L2 VIP; ingress-nginx HA (2 replicas after SPOF fix).
- Namespace `platform-lab` serves via Host `platform-lab.local` → VIP → ingress → Service → Pods.
- **Observed in Project 1:** NetworkPolicy can block traffic; single ingress replica on one worker was a SPOF.

## 5. AWS Environment

- EKS managed control plane; VPC CNI; ALB with **IP** targets; EBS CSI; observability in `observability`.
- **Observed in Project 1:** NetworkPolicy objects may exist without observed enforcement under current networking; EBS is AZ-bound (`ap-south-1b`).

## 6. Platform Architecture

```
Git (desired state) → Jenkins (CI/image) → GitOps promote → Argo CD → Kubernetes
User → DNS/ALB|MetalLB → Ingress → Service → Pod → Node → Storage
```

See [platform-operating-model.svg](../diagrams/platform-operating-model.svg) and architecture docs under `docs/architecture/`.

## 7. Ownership Model

| Domain | Owner |
|---|---|
| Application code | Developer |
| CI build / digest | Jenkins |
| Desired state | Git |
| Reconciliation | Argo CD |
| Infrastructure | Terraform |
| Ops automation | Python / Ansible |
| Incident response | Operator |
| Managed CP / EC2 / EBS APIs | AWS |

Full matrix: [change-ownership.md](./change-ownership.md).

## 8. Source of Truth

- **Git** is the desired-state source for applications and GitOps overlays.
- **Terraform** is the source for provisioned infrastructure (local state in this lab — production gap).
- **Runtime kubectl edits** are not durable under Argo selfHeal (**Observed in Project 1** ~6s selfHeal).

## 9. Change Management

1. Branch → change → validate → review → merge  
2. Jenkins for app changes (skip for GitOps-only when designed)  
3. Digest pin in Git → Argo sync → verify  

Checklists: [pre-change-checklist.md](../checklists/pre-change-checklist.md), [post-change-checklist.md](../checklists/post-change-checklist.md).  
Anti-patterns: [operational-antipatterns.md](./operational-antipatterns.md).

## 10. Deployment Model

- Image tag is mutable reference; **digest** is immutable identity.  
- Known-good: `0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`.  
- Rollback path: **Git rollback → Argo reconcile** (not `kubectl rollout undo` as the normal model).  
  Runbook: [git-rollback.md](../runbooks/git-rollback.md).

## 11. Observability Model

| Signal layer | Tooling |
|---|---|
| Object state | kube-state-metrics |
| Node OS | node-exporter |
| Scrapes / TSDB | Prometheus |
| Dashboards | Grafana |
| Resource metrics / HPA | Metrics Server |

Golden signals: [golden-signals.md](./golden-signals.md).  
Do not confuse Metrics Server with Prometheus.

## 12. Incident Response

Flow: Detect → Acknowledge → Scope → Evidence → Stabilize → Diagnose → Remediate → Verify → Monitor → Close → Postmortem.

Playbook: [incident-response-playbook.md](./incident-response-playbook.md).  
**Stabilization may matter more than immediate root cause.**

## 13. Triage Framework

STEP 1 classify layer → STEP 2 blast radius → STEP 3 Healthy/Degraded/Unavailable → STEP 4 recent changes → STEP 5 evidence before change → STEP 6 smallest safe remediation → STEP 7 verify.

Details: [triage-framework.md](../troubleshooting/triage-framework.md) · [troubleshooting-matrix.md](../troubleshooting/troubleshooting-matrix.md) · [platform-failure-domain.svg](../diagrams/platform-failure-domain.svg).

## 14. Application Operations

- Health: `/health` HTTP 200 (VMware Host header; AWS ALB).  
- Runbooks: [application-unhealthy.md](../runbooks/application-unhealthy.md), [pod-failure.md](../runbooks/pod-failure.md), [pod-not-ready.md](../runbooks/pod-not-ready.md), [failed-rollout.md](../runbooks/failed-rollout.md).  
- **Observed:** Pod delete → ReplicaSet recreate ~10s (VMware). Running ≠ Ready. Bad `0.1.5` left old RS serving.

## 15. Kubernetes Operations

Nodes, Deployments, ReplicaSets, Services, EndpointSlices, events. Prefer READ-ONLY first.  
Node maintenance vs failure: [node-maintenance.md](./node-maintenance.md), [worker-node-failure.md](../runbooks/worker-node-failure.md).

## 16. Argo CD Operations

Statuses: Synced/OutOfSync, Healthy/Degraded/Progressing/Unknown, ComparisonError.  
**Observed:** waves-health ComparisonError when Kustomize could not resolve `../base/namespace.yaml` → Unknown until self-contained kustomization.  
Runbooks: [argo-outofsync.md](../runbooks/argo-outofsync.md), [argo-sync-failure.md](../runbooks/argo-sync-failure.md), [argocd-applicationset-troubleshooting.md](../runbooks/argocd-applicationset-troubleshooting.md), [argocd-appproject-denied.md](../runbooks/argocd-appproject-denied.md).

## 17. Jenkins Operations

Pipeline: checkout → change detection → test → version → build → validate → push → digest → GitOps promote.  
App change = full CI; GitOps-only may skip stages (loop prevention).  
Runbooks: [jenkins-build-failure.md](../runbooks/jenkins-build-failure.md), [jenkins-unavailable.md](../runbooks/jenkins-unavailable.md).

## 18. Networking Operations

VMware: MetalLB → VIP → ingress-nginx → Service → Pods.  
AWS: Internet → ALB (IP targets) → Pod IP.  
**Observed:** VMware ingress SPOF then HA with PDB; NetworkPolicy enforced on VMware lab, not observed enforcing on AWS lab config.  
Runbooks under Networking in [README.md](./README.md).

## 19. Storage Operations

VMware `local-path`; AWS EBS CSI + snapshots.  
**Observed:** AZ affinity for EBS; worker loss ~6.3 min recovery; snapshot Ready ~72s; restore PVC→Running ~15s; cross-namespace restore failed until same-ns VolumeSnapshotContent.  
Runbooks: [pvc-pv-troubleshooting.md](../runbooks/pvc-pv-troubleshooting.md), [ebs-attach-troubleshooting.md](../runbooks/ebs-attach-troubleshooting.md), [ebs-snapshot-restore.md](../runbooks/ebs-snapshot-restore.md).

## 20. Node Operations

**Observed VMware:** kubelet stop → NotReady → capacity drop → recover after kubelet restart.  
**Observed AWS:** worker terminate → StatefulSet recreate needs same-AZ → EBS reattach.  
Do not confuse planned cordon/drain with failure.

## 21. Scaling Operations

HPA + Metrics Server. **Observed:** VMware 2→4 under CPU load; AWS 2→3. Timing varies — do not guarantee.  
Runbook: [hpa-not-scaling.md](../runbooks/hpa-not-scaling.md).

## 22. Security Operations

RBAC, ServiceAccounts (`platform-lab` automount disabled), Pod Security baseline (VMware `v1.31`, AWS `v1.36`), NetworkPolicy.  
Runbooks: [rbac-access-denied.md](../runbooks/rbac-access-denied.md), [pod-security-admission.md](../runbooks/pod-security-admission.md), [security-incident.md](../runbooks/security-incident.md).  
Never log Secret values.

## 23. Automation Operations

`platform-automate doctor|verify|ops health|ops triage|ops report|ops evidence` — ops commands are **READ-ONLY**.  
Ansible: Linux/Jenkins supported; Windows Ansible CLI blocked in this project.  
Runbooks: [python-automation-failure.md](../runbooks/python-automation-failure.md), [ansible-failure.md](../runbooks/ansible-failure.md).

## 24. Backup and DR Operations

Authoritative detail remains Section 25. Index: [disaster-recovery-index.md](../runbooks/disaster-recovery-index.md).  
RPO/RTO ops: [rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md) — lab measurements ≠ production SLA.

## 25. Maintenance

Recommended practice (not all historically executed as Project 1 rituals): [platform-maintenance.md](./platform-maintenance.md).

## 26. Health Checks

Daily: [daily-platform-health.md](../checklists/daily-platform-health.md).  
Automation: `platform-automate ops health`.

## 27. Common Failure Modes

| Mode | Evidence pointer |
|---|---|
| Pod delete / recreate | [pod-failure.md](../runbooks/pod-failure.md) |
| NotReady / endpoints drop | [pod-not-ready.md](../runbooks/pod-not-ready.md) |
| Bad rollout | [failed-rollout.md](../runbooks/failed-rollout.md) |
| Argo ComparisonError | [argo-outofsync.md](../runbooks/argo-outofsync.md) |
| Worker / EBS | [worker-node-failure.md](../runbooks/worker-node-failure.md) |
| Ingress SPOF | [ingress-unavailable.md](../runbooks/ingress-unavailable.md) |
| Grafana OOM (historical) | [../postmortems/grafana-oom.md](../postmortems/grafana-oom.md) |

Coverage honesty: [observed-vs-untested.md](./observed-vs-untested.md).

## 28. Recovery

Prefer: restore Git desired state → Argo reconcile → verify HTTP/Argo/Pods.  
Diagram: [rollback-decision-tree.svg](../diagrams/rollback-decision-tree.svg).  
DR: Section 25 guides; do not destroy EKS/VPC for practice.

## 29. Escalation

Escalate on blast radius, data loss, security, duration, unknown RCE, failed recovery — do not keep risky experimenting.  
[escalation.md](./escalation.md) · [incident-severity.md](./incident-severity.md).

## 30. Evidence Collection

Timestamps, context, namespace, Git SHA, Argo revision, digest, pods, events, logs, metrics, PVC/PV, AWS volume state.  
**Never** passwords, tokens, keys, Secret YAML.  
[incident-evidence.md](./incident-evidence.md) · `platform-automate ops evidence`.

## 31. Postmortem

Template: [postmortem-template.md](../postmortems/postmortem-template.md).  
Historical summaries: [grafana-oom.md](../postmortems/grafana-oom.md), [vmware-ingress-spof.md](../postmortems/vmware-ingress-spof.md), [failed-rollout-0.1.5.md](../postmortems/failed-rollout-0.1.5.md), [vmware-worker-failure.md](../postmortems/vmware-worker-failure.md), [argo-comparison-error.md](../postmortems/argo-comparison-error.md), [cross-namespace-snapshot-restore.md](../postmortems/cross-namespace-snapshot-restore.md). Blame-free; turn lessons into runbook/automation improvements.

## 32. Operational Readiness

Assessment: [operational-readiness-assessment.md](./operational-readiness-assessment.md) (Implemented / Partial / Documented only / Not tested).

## 33. Production Gaps

Potential enhancements (not universal mandates): [production-gaps.md](./production-gaps.md) — alerting, log aggregation, remote TF state, multi-region DR, secret management, SLOs, etc.

## 34. Project 1 Lessons

1. Git digest pin + Argo beats imperative undo for durable recovery.  
2. Running ≠ Ready ≠ Serving.  
3. Ingress HA and PDB matter — **Observed** SPOF then fix.  
4. EBS is AZ topology — worker recovery is storage-aware.  
5. Snapshot restore namespace/VSC rules matter — **Observed** cross-ns failure.  
6. ComparisonError is often source generation, not “cluster down.”  
7. NetworkPolicy enforcement is CNI/config dependent — do not generalize AWS lab non-enforcement.  
8. Measure T0–Tn; lab RTO ≠ SLA.  
9. Evidence before mutation; redact secrets.  
10. Automate READ-ONLY health and evidence packs.

Interview prep: [operations-interview-notes.md](./operations-interview-notes.md).

---

## Operator mental model

1. Observe  
2. Detect  
3. Classify  
4. Scope  
5. Diagnose  
6. Change  
7. Verify  
8. Recover  
9. Document  
10. Improve  

Map: Prometheus/Grafana/KSM → alerts/health → triage framework → runbooks → Git/Argo/TF → checklists → DR → postmortem → Python/Ansible improvements.

Lifecycle: [platform-operations-lifecycle.svg](../diagrams/platform-operations-lifecycle.svg).

---

A good operator does not begin by changing the system.

A good operator begins by:

1. determining impact,  
2. identifying the failure domain,  
3. collecting evidence,  
4. understanding the desired state,  
5. making the smallest safe change,  
6. verifying the result,  
7. preserving what was learned.

The runbook must therefore teach:

**OBSERVE → UNDERSTAND → ACT → VERIFY → LEARN**
