# Platform version inventory

**Last validated:** 2026-09-26 · Do not write "latest" without verification.

## VMware (`ckad-lab`)

| Component | Version / value |
|---|---|
| Kubernetes | **1.31.14** |
| Argo CD | **v3.5.3** |
| Nodes | 3 Ready |
| MetalLB VIP | 192.168.56.200 |
| StorageClass | local-path |
| App | platform-lab **0.1.4** digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |

CNI Calico / ingress-nginx / Prometheus stack: see cluster and `docs/operations/platform-version-inventory.md` for component-level notes.

## AWS (`platform-lab-aws`)

| Component | Version / value |
|---|---|
| EKS Kubernetes | **1.36.4** |
| Argo CD | **v3.1.0** |
| Workers | 2 × t3.medium |
| Region | ap-south-1 |
| Storage | ebs-gp3 / EBS CSI |
| Lab EBS | vol-05faa26874d720ecd · ap-south-1b |
| App | same **0.1.4** digest |

Observability images observed in lab (AWS): Grafana **12.3.1**, Prometheus **v3.14.0**, KSM **v2.20.0** (from running Deployments 2026-09-26).

## Automation workstation

| Tool | Notes |
|---|---|
| Python | venv under `automation/python` |
| platform-automate | 0.1.0 |
| Ansible | Linux/Jenkins path; Windows CLI blocked |
| Terraform | AWS lab toolchain |
| kubectl / Helm | Present on workstation / tools container |

Authoritative ops copy also: [../operations/platform-version-inventory.md](../operations/platform-version-inventory.md)
