# Project 1 Diagrams

Landing page for every diagram in this folder (44 SVGs). All files are pure, self-contained SVG
(no external images, fonts, CSS, or scripts) and are validated as described in
[svg-compatibility-report.md](../portfolio/svg-compatibility-report.md).
Authoring rules: [svg-authoring-guidelines.md](../portfolio/svg-authoring-guidelines.md).

Start with the [Project 1 reference architecture](./project1-reference-architecture.svg).

---

## Architecture

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-reference-architecture.svg](./project1-reference-architecture.svg) | End-to-end architecture: Git → Jenkins / Argo CD → VMware and AWS EKS clusters, data plane vs control flow, automation and DR notes | [architecture/project1-reference-architecture.md](../architecture/project1-reference-architecture.md), [README](../../README.md) |
| [project1-final-study-architecture.svg](./project1-final-study-architecture.svg) | Five flows that never mix: CI, CD, data plane, IaC management, automation, observability | [portfolio/project1-revisit-guide.md](../portfolio/project1-revisit-guide.md) |

## GitOps

| Diagram | Purpose | Related document |
|---|---|---|
| [argo-advanced-gitops-reference.svg](./argo-advanced-gitops-reference.svg) | ApplicationSet, App-of-Apps, sync waves / hooks / options, RBAC, sync windows, AppProject boundary | [architecture/argo-gitops-reference.md](../architecture/argo-gitops-reference.md), [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| [argo-enterprise-gitops-composition.svg](./argo-enterprise-gitops-composition.svg) | How Jenkins CI, Argo CD, AppProject, ApplicationSet and App-of-Apps compose in Project 1 | [architecture/argo-gitops-reference.md](../architecture/argo-gitops-reference.md), [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| [argo-applicationset.svg](./argo-applicationset.svg) | Generator → parameters → template → one generated Application per environment → resources | [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| [argo-app-of-apps.svg](./argo-app-of-apps.svg) | Parent Application managing child Applications with sync waves | [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| [argo-sync-lifecycle.svg](./argo-sync-lifecycle.svg) | Sync order: refresh, diff, PreSync hooks, waves, health, PostSync | [architecture/argo-gitops-reference.md](../architecture/argo-gitops-reference.md), [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| [argo-project-security.svg](./argo-project-security.svg) | AppProject as a security boundary: source repos, destinations, resource kinds | [argo-advanced-patterns.md](../argo-advanced-patterns.md) |

## Automation

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-automation-boundaries.svg](./project1-automation-boundaries.svg) | Which tool owns what (Terraform, Jenkins, Git, Argo CD, Python, Ansible) and anti-patterns | [docs/README.md](../README.md) |
| [project1-automation-reference.svg](./project1-automation-reference.svg) | Delivery path vs separate operational automation path | [automation/automation-architecture.md](../automation/automation-architecture.md) |
| [automation-vs-gitops.svg](./automation-vs-gitops.svg) | Operational automation may commit desired state to Git; Argo CD reconciles | [automation/automation-architecture.md](../automation/automation-architecture.md) |
| [python-automation-stack.svg](./python-automation-stack.svg) | Python CLI → controller → adapters (REST, Kubernetes, AWS, Ansible, Terraform) → verification | [automation/automation-architecture.md](../automation/automation-architecture.md) |
| [python-ansible-orchestration.svg](./python-ansible-orchestration.svg) | Python decides, Ansible configures, Python verifies | [automation/automation-architecture.md](../automation/automation-architecture.md) |
| [ansible-architecture.svg](./ansible-architecture.svg) | Control node, inventory, playbooks, modules, managed nodes | [automation/automation-architecture.md](../automation/automation-architecture.md) |

## Networking

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-control-and-data-plane.svg](./project1-control-and-data-plane.svg) | Control/management path vs user HTTP data path on VMware (MetalLB, ingress-nginx) and AWS (ALB IP targets) | [docs/README.md](../README.md) |

## Storage

| Diagram | Purpose | Related document |
|---|---|---|
| [storage-vmware-vs-aws.svg](./storage-vmware-vs-aws.svg) | Shared Kubernetes storage abstraction, different backends | [aws-storage-statefulset.md](../aws-storage-statefulset.md), [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |
| [vmware-vs-aws-storage-abstraction.svg](./vmware-vs-aws-storage-abstraction.svg) | Same PVC interface, different failure / mobility model | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |
| [vmware-storage-statefulset.svg](./vmware-storage-statefulset.svg) | StatefulSet → PVC → PV → local-path on VMware | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |
| [vmware-storage-pod-recovery.svg](./vmware-storage-pod-recovery.svg) | Pod deletion: same PVC / PV, data survives | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |
| [aws-storage-statefulset.svg](./aws-storage-statefulset.svg) | StatefulSet → PVC → PV → EBS CSI → EBS on EKS | [aws-storage-statefulset.md](../aws-storage-statefulset.md) |
| [aws-storage-pod-recovery.svg](./aws-storage-pod-recovery.svg) | Pod deletion on EKS: same PVC / PV / EBS volume | [aws-storage-statefulset.md](../aws-storage-statefulset.md) |
| [aws-ebs-az-constraint.svg](./aws-ebs-az-constraint.svg) | An EBS volume can only attach in its own Availability Zone | [aws-storage-resilience.md](../aws-storage-resilience.md) |
| [aws-ebs-node-failure-recovery.svg](./aws-ebs-node-failure-recovery.svg) | Same-AZ worker failure: EBS reattach to a replacement worker | [aws-storage-resilience.md](../aws-storage-resilience.md) |
| [storage-resilience-vmware-vs-aws.svg](./storage-resilience-vmware-vs-aws.svg) | Worker-failure behaviour of local-path vs EBS; neither is multi-AZ | [aws-storage-resilience.md](../aws-storage-resilience.md) |

## Security

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-security-architecture.svg](./project1-security-architecture.svg) | Kubernetes vs AWS authorization planes; NetworkPolicy enforcement by CNI | [docs/README.md](../README.md) |
| [kubernetes-security-layers.svg](./kubernetes-security-layers.svg) | Authentication, RBAC, Pod Security Admission, securityContext, NetworkPolicy, Secrets, IAM | [security-rbac.md](../security-rbac.md) |
| [kubernetes-rbac-model.svg](./kubernetes-rbac-model.svg) | Subject → binding → Role / ClusterRole → API decision | [security-rbac.md](../security-rbac.md) |
| [serviceaccount-security.svg](./serviceaccount-security.svg) | ServiceAccount token automount vs `automountServiceAccountToken=false` | [security-rbac.md](../security-rbac.md) |
| [aws-iam-vs-kubernetes-rbac.svg](./aws-iam-vs-kubernetes-rbac.svg) | IAM and Kubernetes RBAC are separate; Pod Identity bridges them | [security-rbac.md](../security-rbac.md) |

## Observability

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-reliability-stack.svg](./project1-reliability-stack.svg) | Health endpoints → probes → workloads → HPA / PDB → Prometheus → runbooks, with observed recovery times | [docs/README.md](../README.md) |

## DR

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-dr-architecture.svg](./project1-dr-architecture.svg) | Recovery sources (Git, Terraform, Argo CD, registry, snapshots) and reconstruct sequence | [docs/README.md](../README.md) |
| [disaster-recovery-architecture.svg](./disaster-recovery-architecture.svg) | GitHub → Argo CD → Kubernetes → storage / snapshot / AWS Backup, with Terraform rebuild | [runbooks/disaster-recovery-index.md](../runbooks/disaster-recovery-index.md), [runbooks/git-argo-recovery.md](../runbooks/git-argo-recovery.md) |
| [dr-dependency-graph.svg](./dr-dependency-graph.svg) | Recovery dependency order on the AWS path | [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md), [runbooks/terraform-infrastructure-recovery.md](../runbooks/terraform-infrastructure-recovery.md) |
| [eks-recovery-flow.svg](./eks-recovery-flow.svg) | Step-by-step EKS incident recovery flow | [runbooks/disaster-recovery-index.md](../runbooks/disaster-recovery-index.md) |
| [ebs-snapshot-recovery.svg](./ebs-snapshot-recovery.svg) | Live volume vs restored snapshot copy | [runbooks/ebs-storage-recovery.md](../runbooks/ebs-storage-recovery.md) |
| [vmware-vs-aws-dr.svg](./vmware-vs-aws-dr.svg) | DR model on VMware vs AWS and the shared recovery planes | [runbooks/disaster-recovery-index.md](../runbooks/disaster-recovery-index.md) |

## Operations

| Diagram | Purpose | Related document |
|---|---|---|
| [platform-operating-model.svg](./platform-operating-model.svg) | Delivery side vs operational side of the platform | [operations/platform-operations-handbook.md](../operations/platform-operations-handbook.md) |
| [platform-operations-lifecycle.svg](./platform-operations-lifecycle.svg) | Observe → detect → triage → diagnose → change → verify → document → improve | [operations/platform-operations-handbook.md](../operations/platform-operations-handbook.md) |
| [platform-failure-domain.svg](./platform-failure-domain.svg) | User path, control-plane path, and cloud control path as separate failure domains | [operations/platform-operations-handbook.md](../operations/platform-operations-handbook.md) |
| [platform-runbook-map.svg](./platform-runbook-map.svg) | Runbook categories | [operations/README.md](../operations/README.md) |
| [rollback-decision-tree.svg](./rollback-decision-tree.svg) | Git rollback + Argo reconcile as the primary rollback path | [operations/platform-operations-handbook.md](../operations/platform-operations-handbook.md) |

## Project 1 Portfolio

| Diagram | Purpose | Related document |
|---|---|---|
| [project1-learning-map.svg](./project1-learning-map.svg) | Conceptual learning order with the tool behind each layer | [portfolio/project1-revisit-guide.md](../portfolio/project1-revisit-guide.md) |
| [project1-learning-dependencies.svg](./project1-learning-dependencies.svg) | Topic dependencies and prerequisites for the hardest stages | [portfolio/project1-revisit-guide.md](../portfolio/project1-revisit-guide.md) |
| [project1-application-lifecycle.svg](./project1-application-lifecycle.svg) | Build, deliver, run, observe, scale, fail, roll back | [portfolio/project1-revisit-guide.md](../portfolio/project1-revisit-guide.md) |
