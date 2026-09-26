# Platform version inventory

Separate **VMware cluster**, **AWS cluster**, and **automation workstation**.  
Mark **Not verified** when not re-checked at Section 26 write time.

Primary pin source: [toolchain-inventory.md](../toolchain-inventory.md).

---

## Kubernetes & platform runtime

| Component | VMware `ckad-lab` | AWS EKS | Label |
|---|---|---|---|
| Kubernetes server | **1.31.14** | **1.36.4** (nodes `v1.36.4-eks-f4fc4f1`) | Observed (baseline inventory) |
| containerd | 2.2.1 | EKS-managed | Observed VMware / AWS managed |
| CNI | Calico/Tigera | VPC CNI | Observed |

---

## GitOps & ingress

| Component | VMware | AWS | Label |
|---|---|---|---|
| Argo CD | **v3.5.3** | **v3.1.0** | Observed |
| ingress | ingress-nginx (2 replicas) | ALB Ingress Controller | Observed |
| MetalLB | VIP pool incl. **192.168.56.200** | N/A | Observed VMware |

---

## Storage CSI

| Component | VMware | AWS | Label |
|---|---|---|---|
| StorageClass | `local-path` | `ebs-gp3` | Observed |
| EBS CSI | N/A | `aws-ebs-csi-driver` v1.66.0-eksbuild.1 (prior doc) | Observed in aws-storage-resilience |
| Snapshot controller | N/A | v8.6.0-eksbuild.8 (DR doc) | Observed in dr-lab-evidence |

---

## Observability (representative)

| Component | VMware | AWS | Label |
|---|---|---|---|
| Prometheus / Grafana | kube-prometheus-stack in `monitoring` | observability stack | Observed baseline |
| metrics-server | Present for HPA lab | Present | Observed pattern |
| kube-state-metrics | Yes | Yes | Observed pattern |
| node-exporter | Yes | Yes | Observed pattern |

Exact chart app versions: **Not verified** in Section 26 — check live `helm list` / Argo when upgrading.

---

## Application artifact

| Field | Value | Label |
|---|---|---|
| Image | `kirandevraaj/platform-lab:0.1.4` | Observed |
| Digest | `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` | Observed |

---

## Workstation / automation (from toolchain inventory)

| Tool | Version | Label |
|---|---|---|
| Python | 3.14.6 (Windows venv) | Observed |
| kubectl | 1.36.1 client | Accept discovered |
| helm | 4.2.3 | Accept discovered |
| git | 2.54 | Accept discovered |
| kubernetes Python client | 32.0.1 pin | Required pin |
| boto3 | 1.40.18 pin | Required pin |
| ansible-core | 2.18.6 pin | Required pin |
| aws CLI on PATH | absent (Windows/WSL snapshot) | Documented absence |
| terraform on PATH | absent | Documented absence |

---

## Related

- [platform-inventory.md](./platform-inventory.md)
- [observed-vs-untested.md](./observed-vs-untested.md)
