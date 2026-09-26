# Operations (Section 26)

Operator landing page for the **Kubernetes Platform Engineering & GitOps Lab**.  
**Master reference:** [platform-operations-handbook.md](./platform-operations-handbook.md)

**Labeling:** **Observed in Project 1** = measured or exercised in lab; **Design guidance** / **Not tested in Project 1** = do not treat as guaranteed production behavior.

---

## Getting Started

| Document | Description |
|---|---|
| [Platform Operations Handbook](./platform-operations-handbook.md) | Sections 1–34; operator mental model |
| [Operations interview notes](./operations-interview-notes.md) | 20 Q&A (Phase 96) |
| [Platform inventory](./platform-inventory.md) | VMware + AWS facts |
| [Golden signals](./golden-signals.md) | Availability, latency, traffic, errors, saturation |
| [Triage framework](../troubleshooting/triage-framework.md) | STEP 1–7 |
| [Troubleshooting matrix](../troubleshooting/troubleshooting-matrix.md) | Symptom → first checks |
| [Operations command reference](./operations-command-reference.md) | READ-ONLY first commands |
| [Dry-run / precondition pattern](./dry-run-precondition-pattern.md) | Check → Plan → Confirm → Execute → Verify |
| [Observed vs untested](./observed-vs-untested.md) | Coverage honesty |
| [Operations interview notes](./operations-interview-notes.md) | 20 Q&A |

---

## Daily Ops

| Document | Description |
|---|---|
| [Daily platform health](../checklists/daily-platform-health.md) | Fast READ-ONLY checklist |
| [Operator shift checklist](../checklists/operator-shift-checklist.md) | Start/end of shift |
| [Platform maintenance](./platform-maintenance.md) | Daily/weekly/monthly cadence |
| [Change ownership](./change-ownership.md) | Who owns Git, Argo, Terraform, CI |

---

## Incident Response

| Document | Description |
|---|---|
| [Incident response playbook](./incident-response-playbook.md) | End-to-end flow |
| [Incident severity](./incident-severity.md) | SEV-1–4 (lab model) |
| [Escalation](./escalation.md) | When to stop experimenting |
| [Incident evidence](./incident-evidence.md) | What to capture (no secrets) |
| [Incident timeline template](./incident-timeline-template.md) | T0–T6 |
| [Operational anti-patterns](./operational-antipatterns.md) | What not to do |

---

## Application

| Runbook | Path |
|---|---|
| Application unhealthy | [../runbooks/application-unhealthy.md](../runbooks/application-unhealthy.md) |
| Pod failure | [../runbooks/pod-failure.md](../runbooks/pod-failure.md) |
| Pod not ready | [../runbooks/pod-not-ready.md](../runbooks/pod-not-ready.md) |
| Failed rollout | [../runbooks/failed-rollout.md](../runbooks/failed-rollout.md) |
| GitOps change | [../runbooks/gitops-change.md](../runbooks/gitops-change.md) |
| Git rollback | [../runbooks/git-rollback.md](../runbooks/git-rollback.md) |
| Docker release failure | [../runbooks/docker-release-failure.md](../runbooks/docker-release-failure.md) |

**App pin:** `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## Kubernetes

| Runbook | Path |
|---|---|
| Worker node failure | [../runbooks/worker-node-failure.md](../runbooks/worker-node-failure.md) |
| Node maintenance (cordon/drain) | [./node-maintenance.md](./node-maintenance.md) |
| Kubernetes API failure | [../runbooks/kubernetes-api-failure.md](../runbooks/kubernetes-api-failure.md) |

Architecture: [../architecture/reliability.md](../architecture/reliability.md)

---

## Argo CD

| Runbook | Path |
|---|---|
| OutOfSync / ComparisonError | [../runbooks/argo-outofsync.md](../runbooks/argo-outofsync.md) |
| Sync failure (hooks/waves) | [../runbooks/argo-sync-failure.md](../runbooks/argo-sync-failure.md) |
| ApplicationSet | [../runbooks/argocd-applicationset-troubleshooting.md](../runbooks/argocd-applicationset-troubleshooting.md) |
| AppProject denied | [../runbooks/argocd-appproject-denied.md](../runbooks/argocd-appproject-denied.md) |
| Controller unavailable | [../runbooks/argocd-controller-unavailable.md](../runbooks/argocd-controller-unavailable.md) |
| Git / Argo recovery | [../runbooks/git-argo-recovery.md](../runbooks/git-argo-recovery.md) |

Reference: [../argo-advanced-patterns.md](../argo-advanced-patterns.md) · [../architecture/argo-gitops-reference.md](../architecture/argo-gitops-reference.md)

---

## Networking

| Runbook | Path |
|---|---|
| Ingress unavailable | [../runbooks/ingress-unavailable.md](../runbooks/ingress-unavailable.md) |
| MetalLB VIP | [../runbooks/metallb-vip-failure.md](../runbooks/metallb-vip-failure.md) |
| AWS ALB unhealthy | [../runbooks/aws-alb-unhealthy.md](../runbooks/aws-alb-unhealthy.md) |
| Service / endpoints | [../runbooks/service-endpoint-troubleshooting.md](../runbooks/service-endpoint-troubleshooting.md) |
| NetworkPolicy | [../runbooks/networkpolicy-troubleshooting.md](../runbooks/networkpolicy-troubleshooting.md) |

VMware: [../vmware-networking-anatomy.md](../vmware-networking-anatomy.md) · AWS: [../architecture/networking.md](../architecture/networking.md)

---

## Storage

| Runbook | Path |
|---|---|
| PVC / PV | [../runbooks/pvc-pv-troubleshooting.md](../runbooks/pvc-pv-troubleshooting.md) |
| EBS attach | [../runbooks/ebs-attach-troubleshooting.md](../runbooks/ebs-attach-troubleshooting.md) |
| EBS snapshot restore | [../runbooks/ebs-snapshot-restore.md](../runbooks/ebs-snapshot-restore.md) |

Labs: [../vmware-storage-statefulset.md](../vmware-storage-statefulset.md) · [../aws-storage-statefulset.md](../aws-storage-statefulset.md) · [../aws-storage-resilience.md](../aws-storage-resilience.md)

---

## Observability

| Runbook | Path |
|---|---|
| Prometheus target down | [../runbooks/prometheus-target-down.md](../runbooks/prometheus-target-down.md) |
| Grafana unavailable | [../runbooks/grafana-unavailable.md](../runbooks/grafana-unavailable.md) |
| Metrics Server | [../runbooks/metrics-server-unavailable.md](../runbooks/metrics-server-unavailable.md) |
| KSM / node-exporter | [../runbooks/kube-observability-troubleshooting.md](../runbooks/kube-observability-troubleshooting.md) |
| HPA not scaling | [../runbooks/hpa-not-scaling.md](../runbooks/hpa-not-scaling.md) |

Architecture: [../architecture/observability.md](../architecture/observability.md)

---

## Security

| Runbook | Path |
|---|---|
| RBAC access denied | [../runbooks/rbac-access-denied.md](../runbooks/rbac-access-denied.md) |
| ServiceAccount | [../runbooks/serviceaccount-troubleshooting.md](../runbooks/serviceaccount-troubleshooting.md) |
| Pod Security Admission | [../runbooks/pod-security-admission.md](../runbooks/pod-security-admission.md) |
| Security incident | [../runbooks/security-incident.md](../runbooks/security-incident.md) |

Reference: [../security-rbac.md](../security-rbac.md)

---

## Automation

| Runbook | Path |
|---|---|
| Python automation | [../runbooks/python-automation-failure.md](../runbooks/python-automation-failure.md) |
| Ansible | [../runbooks/ansible-failure.md](../runbooks/ansible-failure.md) |
| Automation (general) | [../runbooks/automation-failure.md](../runbooks/automation-failure.md) |
| Terraform plan | [../runbooks/terraform-plan-failure.md](../runbooks/terraform-plan-failure.md) |
| Terraform apply safety | [../runbooks/terraform-apply-safety.md](../runbooks/terraform-apply-safety.md) |
| Jenkins build | [../runbooks/jenkins-build-failure.md](../runbooks/jenkins-build-failure.md) |
| Jenkins unavailable | [../runbooks/jenkins-unavailable.md](../runbooks/jenkins-unavailable.md) |

Guides: [../automation/platform-automation-master-guide.md](../automation/platform-automation-master-guide.md) · [../toolchain-inventory.md](../toolchain-inventory.md)

---

## DR

**Do not duplicate Section 25 detail here** — use authoritative DR docs:

| Document | Path |
|---|---|
| DR master guide | [../disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) |
| Lab evidence (timings) | [../dr-lab-evidence.md](../dr-lab-evidence.md) |
| RPO/RTO operator guide | [./rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md) |
| DR runbook index | [../runbooks/disaster-recovery-index.md](../runbooks/disaster-recovery-index.md) |
| AWS EKS DR | [../runbooks/aws-eks-disaster-recovery.md](../runbooks/aws-eks-disaster-recovery.md) |
| EBS storage recovery | [../runbooks/ebs-storage-recovery.md](../runbooks/ebs-storage-recovery.md) |

---

## Checklists

| Checklist | Path |
|---|---|
| Daily health | [../checklists/daily-platform-health.md](../checklists/daily-platform-health.md) |
| Pre-change | [../checklists/pre-change-checklist.md](../checklists/pre-change-checklist.md) |
| Post-change | [../checklists/post-change-checklist.md](../checklists/post-change-checklist.md) |
| Operator shift | [../checklists/operator-shift-checklist.md](../checklists/operator-shift-checklist.md) |

---

## Postmortems

| Document | Path |
|---|---|
| Template | [../postmortems/postmortem-template.md](../postmortems/postmortem-template.md) |
| Grafana OOM | [../postmortems/grafana-oom.md](../postmortems/grafana-oom.md) |
| VMware ingress SPOF | [../postmortems/vmware-ingress-spof.md](../postmortems/vmware-ingress-spof.md) |
| Failed rollout 0.1.5 | [../postmortems/failed-rollout-0.1.5.md](../postmortems/failed-rollout-0.1.5.md) |
| VMware worker failure | [../postmortems/vmware-worker-failure.md](../postmortems/vmware-worker-failure.md) |
| Argo ComparisonError | [../postmortems/argo-comparison-error.md](../postmortems/argo-comparison-error.md) |
| Cross-namespace snapshot restore | [../postmortems/cross-namespace-snapshot-restore.md](../postmortems/cross-namespace-snapshot-restore.md) |

---

## Diagrams (Section 26)

| Diagram | Path |
|---|---|
| Failure domain | [../diagrams/platform-failure-domain.svg](../diagrams/platform-failure-domain.svg) |
| Rollback decision tree | [../diagrams/rollback-decision-tree.svg](../diagrams/rollback-decision-tree.svg) |
| Operations lifecycle | [../diagrams/platform-operations-lifecycle.svg](../diagrams/platform-operations-lifecycle.svg) |
| Runbook map | [../diagrams/platform-runbook-map.svg](../diagrams/platform-runbook-map.svg) |
| Operating model | [../diagrams/platform-operating-model.svg](../diagrams/platform-operating-model.svg) |

---

## External dependencies

| Runbook | Path |
|---|---|
| GitHub unavailable | [../runbooks/github-unavailable.md](../runbooks/github-unavailable.md) |
| Registry unavailable | [../runbooks/registry-unavailable.md](../runbooks/registry-unavailable.md) |

---

## Readiness & gaps

| Document | Path |
|---|---|
| Version inventory | [./platform-version-inventory.md](./platform-version-inventory.md) |
| Operational readiness | [./operational-readiness-assessment.md](./operational-readiness-assessment.md) |
| Production gaps | [./production-gaps.md](./production-gaps.md) |

---

## Runbook template

All runbooks follow: [../runbooks/runbook-template.md](../runbooks/runbook-template.md) (READ-ONLY / SAFE MUTATION / DESTRUCTIVE).
