# Project 1 — Environment Map (historical vs current)

**Purpose:** separate what Project 1 *ran* from what exists *now*.
**Companion:** [project1-revisit-guide.md](./project1-revisit-guide.md) · [project1-stage-cheat-sheet.md](./project1-stage-cheat-sheet.md)

Project 1 is finished and frozen as a portfolio project. The Git repository is the archive. Both live environments were later retired on purpose, each in a different way:

| Environment | Historical Project 1 runtime | Current state (after 2026-09-26) | Evidence |
|---|---|---|---|
| VMware `ckad-lab` | Full Project 1 platform | **Basic reusable kubeadm lab** (Project 1 add-ons removed) | [operations/vmware-lab-cleanup.md](../operations/vmware-lab-cleanup.md) |
| AWS `platform-lab-aws` (EKS) | EKS platform built by Terraform | **Project 1 runtime destroyed**; Terraform state empty | [operations/aws-lab-teardown.md](../operations/aws-lab-teardown.md) |
| Git repository | Source of truth for everything | **Unchanged archive**; nothing deleted | this repository |
| Docker Hub | `kirandevraaj/platform-lab` release images | Not touched by teardown or cleanup | [README.md](../../README.md) |

> Rule for reading older documents: most of `docs/` was written while the environments were running. Words like "running", "Healthy", "current", or "live" in those documents describe the **historical runtime**, not today.

---

## 1. Historical VMware Project 1 platform

**Context:** `ckad-lab` · **Kubernetes:** 1.31.14 · **Runtime:** containerd 2.2.1 · **Host:** VMware Workstation Pro, host-only network `192.168.56.0/24`.
**Primary source:** [architecture/architecture-overview.md](../architecture/architecture-overview.md)

| Layer | What ran | Where to read |
|---|---|---|
| Nodes | `k8s-ctrl-01` 192.168.56.10 · `k8s-worker-01` .11 · `k8s-worker-02` .12 (Ubuntu 24.04.4) | [architecture/architecture-overview.md](../architecture/architecture-overview.md) |
| CNI | Calico v3.30.7 (Tigera operator), pod CIDR `10.244.0.0/16`, VXLAN CrossSubnet | [vmware-networking-anatomy.md](../vmware-networking-anatomy.md) |
| Load balancer IPs | MetalLB v0.16.1 L2, pool `lab-pool` `192.168.56.200-210`; ingress VIP `.200`, Grafana `.201` | [architecture/networking.md](../architecture/networking.md) |
| Ingress | ingress-nginx (chart 4.15.1 / controller v1.15.1); single replica at first, then **2 replicas + PDB** | [vmware-ingress-ha.md](../vmware-ingress-ha.md) |
| GitOps | Argo CD **v3.5.3** in `argocd`; Applications `platform-lab-local`, `platform-lab-observability`, `platform-storage-vmware`, `platform-security-vmware`, advanced-lab apps and ApplicationSets | [../../gitops/README.md](../../gitops/README.md) · [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| Application | `platform-lab` namespace, 2 replicas, HPA min 2 / max 4, PDB `minAvailable: 1`, `0.1.4` digest | [architecture/reliability.md](../architecture/reliability.md) |
| Observability | kube-prometheus-stack 91.5.1 in `monitoring` (Prometheus, Grafana, KSM, node-exporter); Metrics Server in `kube-system` | [vmware-observability-anatomy.md](../vmware-observability-anatomy.md) |
| Storage | `local-path` StorageClass; StatefulSet `storage-demo` in `storage-lab` | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |
| Security | `security-lab` namespace: ServiceAccounts, Roles, ClusterRoles, PSA labels, NetworkPolicies | [security-rbac.md](../security-rbac.md) |
| Automation | `automation-lab` namespace (the only namespace the Python CLI may mutate) | [automation/platform-automation-master-guide.md](../automation/platform-automation-master-guide.md) |
| DR drills | Git / Argo Application / namespace recovery drills | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| CI (outside cluster) | Jenkins controller + agent on Docker Desktop (not a deploy target) | [../../jenkins/README.md](../../jenkins/README.md) |

## 2. Historical AWS Project 1 platform

**Historical runtime:** AWS EKS Project 1 environment. **Current:** AWS runtime destroyed after portfolio completion.
**Primary sources:** [../../terraform/aws/README.md](../../terraform/aws/README.md) · [architecture/project1-reference-architecture.md](../architecture/project1-reference-architecture.md)

| Layer | What ran (historical) | Where to read |
|---|---|---|
| Region / network | `ap-south-1`, VPC `10.50.0.0/16`, 2 AZs (`ap-south-1a`, `ap-south-1b`), single NAT gateway | [../../terraform/aws/README.md](../../terraform/aws/README.md) |
| Cluster | EKS **1.36.4** (`platform-lab-aws-lab-eks`), managed control plane | [adr/002-eks-managed-control-plane.md](../adr/002-eks-managed-control-plane.md) |
| Nodes | 2 × t3.small at first, then **2 × t3.medium** (pod density 11 → 17 per node) | [aws-observability-capacity-analysis.md](../aws-observability-capacity-analysis.md) |
| Ingress | AWS Load Balancer Controller → ALB, **target-type ip** | [adr/007-aws-alb-vs-vmware-ingress.md](../adr/007-aws-alb-vs-vmware-ingress.md) |
| GitOps | Separate Argo CD **v3.1.0** (Helm chart 8.3.0), bootstrapped by Terraform; Application `platform-lab-aws` | [architecture/argo-gitops-reference.md](../architecture/argo-gitops-reference.md) |
| Observability | Lightweight Prometheus + Grafana (`observability` ns), KSM + node-exporter, Terraform-installed Metrics Server | [aws-lightweight-observability.md](../aws-lightweight-observability.md) · [kubernetes-platform-observability.md](../kubernetes-platform-observability.md) |
| Storage | EBS CSI add-on, StorageClass `ebs-gp3`, VolumeSnapshotClass `ebs-csi-snapclass`, snapshot-controller | [aws-storage-statefulset.md](../aws-storage-statefulset.md) · [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Security | `security-lab` (same RBAC matrix as VMware); NetworkPolicy objects present but enforcement **not observed** on VPC CNI | [security-rbac.md](../security-rbac.md) |
| Freeze state | `platform-observability-aws` Synced/Degraded (Grafana surge pod Pending: Too many pods) | [aws-observability-degraded-final-state.md](./aws-observability-degraded-final-state.md) |

## 3. Current reusable VMware lab (verified read-only on 2026-09-27)

This is now a **basic reusable lab**, not the full Project 1 runtime.

| Item | Current value |
|---|---|
| Context | `ckad-lab` (kept in local kubeconfig) |
| Nodes | 3 Ready: `k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02` |
| Kubernetes | v1.31.14 |
| Runtime | containerd 2.2.1 |
| CNI | Calico (Tigera operator; `calico-system`, `calico-apiserver`, `tigera-operator`) |
| DNS / proxy | CoreDNS (2/2), kube-proxy |
| Metrics | Metrics Server 1/1 — `kubectl top nodes` works |
| Storage | `local-path` (default), `rancher.io/local-path`, `WaitForFirstConsumer`, provisioner Running |
| Namespaces | `kube-system`, `default`, `kube-public`, `kube-node-lease`, `calico-system`, `calico-apiserver`, `tigera-operator`, `local-path-storage` |
| Helm releases | none |
| Removed | Argo CD, kube-prometheus-stack (Prometheus, Grafana, KSM, node-exporter), ingress-nginx, MetalLB, all Project 1 namespaces, Project 1 ClusterRoles and CRDs |

Remaining CRDs on the cluster: Calico/Tigera, plus Gateway API, Istio, Envoy Gateway and Traefik CRD groups. This repository never installed the last four (no Project 1 manifest references them), so the cleanup left them alone. Their origin is not recorded here.

```text
                 kubeadm cluster (ckad-lab)
                       |
          +------------+------------+
          |            |            |
      ctrl-01      worker-01    worker-02
          |
       Kubernetes 1.31.14 (containerd)
          |
   +------+------+------+
   |      |      |      |
 Calico CoreDNS kube-proxy Metrics Server
                         |
                    local-path
```

Cleanup validation (see [operations/vmware-lab-cleanup.md](../operations/vmware-lab-cleanup.md)): 3 nodes Ready, Calico healthy, `kubectl top` works, nginx Deployment + Service + DNS, pod-to-Service HTTP, and local-path persistence across Pod recreation all passed.

## 4. Current AWS state

| Item | State |
|---|---|
| Project 1 EKS cluster, node groups, VPC, NAT, EIP, ALB, EBS volume, Terraform IAM, add-ons | **Destroyed** 2026-09-26 (52-resource destroy plan; 4 resources removed in a second apply after manual orphan cleanup) |
| AWS account, IAM user `kiran-admin`, default VPC, unrelated target group `lab-web-tg` | Preserved |
| Terraform state | Empty after teardown |
| Self-owned EBS snapshots | 0 |
| Local `platform-lab-aws` kubeconfig context | May still exist locally; it points at a cluster that no longer exists |

## 5. AWS rebuildability

The AWS runtime was intentionally destroyed. The source remains:

| Layer | Source |
|---|---|
| Infrastructure | [../../terraform/aws/](../../terraform/aws/) (VPC, IAM, EKS, LBC, Metrics Server, Argo CD, GitOps bootstrap, EBS CSI, snapshot controller) |
| Tooling container | [../../tools/aws/README.md](../../tools/aws/README.md) |
| Kubernetes desired state | [../../kubernetes/overlays/aws/](../../kubernetes/overlays/aws/) · [../../kubernetes/storage-lab-aws/](../../kubernetes/storage-lab-aws/) · [../../kubernetes/security-lab-aws/](../../kubernetes/security-lab-aws/) |
| Argo CD definitions | [../../gitops/applications/](../../gitops/applications/) · [../../gitops/projects/](../../gitops/projects/) |
| Observability values | [../../observability/aws/](../../observability/aws/) |
| Automation | [../../automation/](../../automation/) |
| Procedures | [terraform-recovery-runbook.md](../terraform-recovery-runbook.md) · [runbooks/terraform-infrastructure-recovery.md](../runbooks/terraform-infrastructure-recovery.md) · [runbooks/aws-eks-disaster-recovery.md](../runbooks/aws-eks-disaster-recovery.md) |

**Status:** rebuildable from source. After teardown, `terraform plan` proposed recreating the full lab, which is what an empty state should do. **The rebuild was not run after the final teardown**, and a full destructive rebuild drill was never part of Project 1 ([dr-lab-evidence.md](../dr-lab-evidence.md)).

## 6. Which stages touched which environment

| Stage (see revisit guide) | VMware | AWS | Live now? |
|---|---|---|---|
| 1 Foundation | Yes | — | Base cluster yes |
| 2 FastAPI + Docker | — (build) | — | Images were published to Docker Hub (not re-checked); not deployed |
| 3 Kustomize packaging | Yes | overlay files only | No |
| 4 Jenkins CI | — (Docker Desktop) | — | Not inspected |
| 5 Argo CD GitOps | Yes | — | No |
| 6 CI → GitOps promotion | Yes | — | No |
| 7 Ingress, NetworkPolicy, MetalLB | Yes | — | No |
| 8 Prometheus / Grafana | Yes | — | No |
| 9 HPA / PDB / rollouts | Yes | — | No |
| 10 Terraform EKS | — | Yes | Destroyed |
| 11 Multi-env digest promotion | Yes | Yes | No |
| 12 AWS capacity, obs, HPA load test | — | Yes | Destroyed |
| 13 KSM, node-exporter, SRE dashboards | Yes | Yes | No |
| 14 Pod / Argo self-healing, readiness | Yes | — | No |
| 15 Failed rollout 0.1.5 + rollback | Yes (AWS stayed Ready by design) | overlay updated | No |
| 16 Worker node failure | Yes | — | No |
| 17 Networking anatomy + ingress HA | Yes | — | No |
| 18 local-path StatefulSet | Yes | — | local-path yes; `storage-lab` no |
| 19 EBS + node/AZ resilience | — | Yes | Destroyed |
| 20 Security / RBAC | Yes | Yes | No |
| 21 Advanced Argo CD | Yes | — | No |
| 22 Python / Ansible | `automation-lab` | Boto3 concepts | CLI source only |
| 23 DR drills | Git/Argo/namespace | EBS snapshot | No |
| 24 Operations handbook | docs | docs | Documentation |
| 25 Portfolio packaging | docs | docs | Documentation |
| 26 Teardown + cleanup | cleanup | teardown | Current state |
