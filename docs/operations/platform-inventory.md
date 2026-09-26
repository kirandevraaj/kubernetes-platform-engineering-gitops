# Platform inventory (operations view)

Snapshot aligned with [dr-baseline-inventory.md](../dr-baseline-inventory.md) and Section 26 platform facts. **No secrets.**

---

## VMware — `ckad-lab`

| Category | Value | Label |
|---|---|---|
| Kubernetes | **1.31.14** | Observed |
| Nodes | 3 Ready (`k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02`) | Observed |
| CNI | Calico / Tigera | Observed |
| StorageClass | `local-path` (default) | Observed |
| Ingress | ingress-nginx **2/2** replicas HA | Observed |
| Load balancing | MetalLB VIP **192.168.56.200** | Observed |
| Argo CD | **v3.5.3** | Observed |
| App `platform-lab` | `0.1.4` digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` | Observed |
| Observability | `monitoring` — Prometheus, Grafana, KSM, node-exporter | Observed |
| NetworkPolicy | Enforced for lab tests | **Observed in Project 1** — [security-rbac.md](../security-rbac.md) |

Deep dive: [vmware-storage-statefulset.md](../vmware-storage-statefulset.md), [vmware-networking-anatomy.md](../vmware-networking-anatomy.md).

---

## AWS — `platform-lab-aws`

| Category | Value | Label |
|---|---|---|
| Cluster | `platform-lab-aws-lab-eks` | Observed |
| Kubernetes | **1.36.4** (`ap-south-1`) | Observed |
| Workers | **2 × t3.medium** (managed node group) | Observed |
| StorageClass | `ebs-gp3` / EBS CSI | Observed |
| Lab volume | `vol-05faa26874d720ecd` · **ap-south-1b** | Observed |
| Ingress | **ALB** (IP targets) | Observed |
| Argo CD | **v3.1.0** | Observed |
| App `platform-lab` | Same image digest as VMware | Observed |
| Observability | `observability` namespace | Observed |
| NetworkPolicy | Objects exist; enforcement **not observed** with VPC CNI setup | **Observed in Project 1** |

Deep dive: [aws-storage-statefulset.md](../aws-storage-statefulset.md), [aws-storage-resilience.md](../aws-storage-resilience.md), [architecture/networking.md](../architecture/networking.md).

---

## Shared GitOps / CI

| Component | Location |
|---|---|
| Git repo | This repository |
| Jenkins | Docker Compose on workstation (`jenkins/`) |
| Terraform (AWS) | `terraform/aws` — local state (**Observed** risk) |
| Automation | `automation/python`, `automation/ansible` |

---

## Application inventory

| Field | Value |
|---|---|
| Namespace | `platform-lab` |
| Deployment | `platform-lab` |
| Replicas (baseline) | 2 |
| Health path | `/health` |
| Metrics path | `/metrics` |

---

## Related

- [platform-version-inventory.md](./platform-version-inventory.md)
- [golden-signals.md](./golden-signals.md)
- [toolchain-inventory.md](../toolchain-inventory.md)
