# Disaster Recovery — Baseline Inventory

**Captured:** 2026-09-26 (Section 25 Phase 1, read-only)  
**Project:** Kubernetes Platform Engineering & GitOps Lab  
**Rule:** No credentials, tokens, kubeconfigs, or secret values recorded here.

---

## 1. VMware lab (`ckad-lab`)

| Field | Value |
|---|---|
| Context | `ckad-lab` |
| Kubernetes | **1.31.14** |
| Nodes | `k8s-ctrl-01` (control-plane), `k8s-worker-01`, `k8s-worker-02` — all **Ready** |
| Node OS | Ubuntu 24.04.4 LTS |
| Runtime | containerd 2.2.1 |
| CNI | Calico / Tigera |

### Namespaces (selected)

`argocd`, `platform-lab`, `storage-lab`, `security-lab`, `monitoring`, `ingress-nginx`, `automation-lab`, `argo-advanced-*`, `argo-child-*`, `argo-nested-*`, system namespaces.

### Argo CD Applications (Synced/Healthy at inventory)

| Application | Notes |
|---|---|
| `platform-lab-local` | Production-like app |
| `platform-lab-observability` | kube-prometheus-stack |
| `platform-storage-vmware` | storage-lab |
| `platform-security-vmware` | security-lab |
| Advanced lab apps | App-of-apps / ApplicationSets (learning) |

### AppProjects

`default`, `platform-lab`, `platform-lab-observability`, `platform-storage-vmware`, `platform-security-vmware`, `platform-advanced-lab`

### ApplicationSets

`platform-advanced-cluster-set`, `platform-advanced-env-set`, `platform-advanced-set`, `platform-nested-list-set`

### Storage

| Item | Value |
|---|---|
| StorageClass | `local-path` (default) |
| PVC `storage-lab/data-storage-demo-0` | Bound → local-path PV |
| CSI drivers | `csi.tigera.io` (ephemeral Calico) |

### Workloads (health)

| Namespace | Status |
|---|---|
| `platform-lab` | Deployment 2/2; image digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |
| `storage-lab` | StatefulSet `storage-demo` 1/1 |
| `security-lab` | 5 Deployments Ready |
| `monitoring` | Grafana, KSM, operator, Prometheus STS Ready |
| `ingress-nginx` | controller 2/2; LB VIP `192.168.56.200` |

### RBAC counts (approximate)

| Kind | Count |
|---|---|
| ServiceAccounts | 92 |
| Roles + RoleBindings | 54 |
| ClusterRoles + ClusterRoleBindings | 183 |

---

## 2. AWS EKS (`platform-lab-aws`)

Accessed via `platform-aws-tools` container (`kubectl` context alias `platform-lab-aws`).

| Field | Value |
|---|---|
| Cluster | `platform-lab-aws-lab-eks` |
| Status | ACTIVE |
| Kubernetes | **1.36** / nodes **v1.36.4-eks-f4fc4f1** |
| Platform version | eks.14 |
| Region | `ap-south-1` |
| Authentication mode | **API_AND_CONFIG_MAP** |
| VPC | `vpc-00c54a2d05f84fed6` (`10.50.0.0/16`) |
| Private subnets | `subnet-00f3786cff1624a1b` (1a), `subnet-036ba63f6c37d5bf0` (1b) |
| Public subnets | `subnet-035e7997872214952` (1a), `subnet-07e630aaa1cad4ec0` (1b) |
| Endpoint | public + private; public CIDR restricted to workstation IP |
| Node group | `platform-lab-aws-lab-managed` — ACTIVE, t3.medium, desired 2 (min 1 / max 3) |

### Nodes

| Node | AZ (from prior lab) | Status |
|---|---|---|
| `ip-10-50-41-156…` | ap-south-1a | Ready |
| `ip-10-50-49-63…` | ap-south-1b | Ready |

### Namespaces

`argocd`, `platform-lab`, `storage-lab`, `security-lab`, `observability`, system namespaces.

### Argo CD Applications (Synced/Healthy)

| Application | Project |
|---|---|
| `platform-lab-aws` | `platform-lab-aws` |
| `platform-storage-aws` | `platform-storage-aws` |
| `platform-security-aws` | `platform-security-aws` |
| `platform-observability-aws` | `platform-observability-aws` |
| `platform-k8s-metrics-aws` | `platform-k8s-metrics-aws` |

ApplicationSets on AWS Argo: **none**.

### EKS add-ons (inventory)

| Add-on | Version | Status |
|---|---|---|
| `aws-ebs-csi-driver` | v1.66.0-eksbuild.1 | ACTIVE |
| `coredns` | v1.14.6-eksbuild.4 | ACTIVE |
| `eks-pod-identity-agent` | v1.4.0-eksbuild.2 | ACTIVE |
| `kube-proxy` | v1.36.0-eksbuild.25 | ACTIVE |
| `vpc-cni` | v1.23.1-eksbuild.1 | ACTIVE |
| `snapshot-controller` | **not installed** at inventory | — |

### Storage

| Item | Value |
|---|---|
| StorageClass | `ebs-gp3` (WaitForFirstConsumer), also `gp2` |
| CSI drivers | `ebs.csi.aws.com`, `efs.csi.aws.com` |
| PVC | `storage-lab/data-storage-demo-0` Bound |
| PV | `pvc-612d84fb-dbd4-46d9-a17f-735216f0594d` |
| EBS volume | **`vol-05faa26874d720ecd`** · 1 GiB · **ap-south-1b** · in-use |
| VolumeSnapshot CRDs | **Absent** at inventory |
| Existing EBS snapshots for this volume | **None** (owner self) |

### Workloads

| Namespace | Status |
|---|---|
| `platform-lab` | 2/2; digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |
| `storage-lab` | `storage-demo-0` Running; `state.txt` present (aws-ebs-storage-lab-001) |
| `security-lab` | 5 Deployments Ready |
| `observability` | grafana, kube-state-metrics, prometheus-server Ready |
| ALB controller | `aws-load-balancer-controller` 2/2 in `kube-system` |
| Ingress | `platform-lab` → ALB `k8s-platform-platform-4c216154e7-…ap-south-1.elb.amazonaws.com` |

---

## 3. Git / Terraform / Backup posture

| Plane | State |
|---|---|
| Git | Source of desired config (apps, Argo manifests, Terraform code, docs) |
| Terraform backend | **Local state** (`terraform/aws/terraform.tfstate`) — gitignored |
| AWS Backup vaults | `aws/efs/automatic-backup-vault` only (EFS automatic; 0 recovery points listed) |
| AWS Backup plans | `aws/efs/automatic-backup-plan` only |
| Protected resources (list) | **Empty** — EKS cluster **not** protected by AWS Backup at inventory |
| Docker artifact | `kirandevraaj/platform-lab:0.1.4` @ digest above |

---

## 4. Safety boundaries for Section 25

**Do not destroy / delete:** main EKS cluster, VPC, `platform-lab`, `storage-lab` production-like workloads, `security-lab`, `observability`/`monitoring`, original EBS `vol-05faa26874d720ecd`, Argo global config unrelated to disposable DR apps.

**Disposable labs allowed:** `dr-lab`, `dr-storage-restore`, temporary VolumeSnapshots / restored volumes / test Applications.

---

## 5. Inventory conclusion

Both clusters are healthy. Persistent application data on AWS is a single AZ-scoped EBS volume without an existing snapshot. Configuration is recoverable from Git + Terraform; data is not. CSI snapshot controller and VolumeSnapshot CRDs are missing and are a prerequisite for the EBS snapshot restore drill.
