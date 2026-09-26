# Kubernetes Platform Engineering & GitOps Lab

End-to-end **Kubernetes platform engineering lab** across **VMware kubeadm** and **AWS EKS**, with Terraform-managed infrastructure, Jenkins CI, GitOps delivery with Argo CD, immutable image promotion, Prometheus/Grafana observability, Kubernetes security, resilience testing, persistent storage, disaster recovery drills, and Python/Ansible automation.

**Portfolio / lab platform** — not a production customer deployment.

**Repository:** [github.com/kirandevraaj/kubernetes-platform-engineering-gitops](https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops)  
**Image:** [hub.docker.com/r/kirandevraaj/platform-lab](https://hub.docker.com/r/kirandevraaj/platform-lab) · `0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## What This Project Demonstrates

| Capability | Notes |
|---|---|
| Dual-environment Kubernetes | VMware `ckad-lab` (1.31.14) + EKS `platform-lab-aws` (1.36.4) |
| IaC | Terraform for VPC, EKS, node groups, IAM, add-ons |
| CI | Jenkins: test → build → push → digest → GitOps promote |
| GitOps | Separate Argo CD control planes; Kustomize overlays |
| Immutable promotion | Same digest across environments |
| Observability | Prometheus, Grafana, KSM, node-exporter, Metrics Server |
| Reliability | HPA, PDB, topology, controlled failure experiments |
| Networking | MetalLB + ingress-nginx (VMware); ALB IP targets (AWS) |
| Storage | local-path (VMware); EBS CSI + snapshots (AWS) |
| Security | RBAC, Pod Security, NetworkPolicy, dedicated SAs |
| Automation | Python CLI, Boto3 concepts, Ansible (Linux/Jenkins) |
| DR / ops | Measured RPO/RTO lab drills; runbooks & handbook |

Story: **BUILD → DEPLOY → OBSERVE → SCALE → SECURE → FAIL → RECOVER → AUTOMATE → OPERATE → DOCUMENT**

---

## Architecture

![Project 1 reference architecture](docs/diagrams/project1-reference-architecture.svg)

Deep dive: [docs/architecture/project1-reference-architecture.md](docs/architecture/project1-reference-architecture.md) · [ADRs](docs/adr/README.md) · [Portfolio](docs/portfolio/README.md)

---

## Environments

| | VMware | AWS |
|---|---|---|
| Context | `ckad-lab` | `platform-lab-aws` |
| Kubernetes | **1.31.14** | **1.36.4** (EKS) |
| Nodes | 3 Ready | 2 × t3.medium |
| Ingress | MetalLB `192.168.56.200` → ingress-nginx | ALB (target-type **ip**) |
| Storage | `local-path` | `ebs-gp3` / EBS CSI |
| Argo CD | **v3.5.3** | **v3.1.0** (separate) |

---

## Capability Matrix

| Capability | Implementation | Verified |
|---|---|---|
| Kubernetes | Yes | Yes |
| Terraform (AWS) | Yes | Yes (lab apply; no destructive rebuild drill) |
| Jenkins CI | Yes | Yes |
| Docker / digest promote | Yes | Yes (`0.1.4`) |
| Git desired state | Yes | Yes |
| Argo CD | Yes | Yes |
| ApplicationSet / App-of-Apps | Yes | Yes (lab apps) |
| Kustomize overlays | Yes | Yes |
| Prometheus / Grafana | Yes | Yes (VMware Healthy; AWS see limitations) |
| KSM / node-exporter | Yes | Yes |
| Metrics Server | Yes | Yes |
| HPA | Yes | Yes (VMware 2→4; AWS 2→3) |
| RBAC / Pod Security | Yes | Yes |
| NetworkPolicy | Yes | **Partial** (VMware enforced; AWS objects present, enforcement not observed) |
| EBS CSI + snapshots | Yes | Yes |
| Python automation CLI | Yes | Yes |
| Boto3 | Yes | **Partial** (code/docs; live Windows workstation path limited) |
| Ansible | Yes | **Partial** (Linux/Jenkins; Windows CLI blocked) |
| DR / RPO-RTO measurements | Yes | **Partial** (selected drills; not full EKS rebuild / AWS Backup restore) |
| Runbooks / ops handbook | Yes | Yes |

---

## Technology Stack

Kubernetes · Terraform · Jenkins · Docker · GitHub · Argo CD · Kustomize · Prometheus · Grafana · kube-state-metrics · node-exporter · Metrics Server · Calico · MetalLB · ingress-nginx · AWS LB Controller / ALB · EBS CSI · CSI snapshots · Python · Boto3 · Ansible · Helm · kubectl

---

## CI/CD · GitOps · Infrastructure · Automation

- **Jenkins:** checkout → change detection → test → build → push → digest → promote overlays (GitOps-only changes skip app CI by design).
- **Argo CD:** reconciles Git → cluster; selfHeal observed (~6s lab).
- **Terraform:** AWS VPC/EKS/IAM/add-ons (local state — production gap).
- **Python / Ansible:** operational automation; ops commands are read-only (`platform-automate ops health|triage|report|evidence`).

---

## Observability · Security · Reliability · Storage · DR · Operations

| Area | Pointer |
|---|---|
| Observability | [docs/architecture/observability.md](docs/architecture/observability.md) |
| Security | [docs/security-rbac.md](docs/security-rbac.md) |
| Reliability | [docs/architecture/reliability.md](docs/architecture/reliability.md) |
| Storage | [docs/aws-storage-statefulset.md](docs/aws-storage-statefulset.md) · [docs/vmware-storage-statefulset.md](docs/vmware-storage-statefulset.md) |
| DR | [docs/disaster-recovery-master-guide.md](docs/disaster-recovery-master-guide.md) |
| Operations | [docs/operations/README.md](docs/operations/README.md) |

---

## Failure Engineering Performed

| Failure | Observed result |
|---|---|
| Pod deleted | ReplicaSet recreate ~**10s** (VMware) |
| Readiness failure | Running ≠ Ready; endpoints drop; no RS replace |
| Failed rollout `0.1.5` | Old RS kept serving; Git rollback to `0.1.4` digest → Argo recover |
| Argo drift / selfHeal | Live edit reverted ~**6s** |
| Argo ComparisonError | Kustomize path error → Unknown until source fixed |
| Worker (VMware kubelet) | NotReady → capacity drop → recover after kubelet |
| Worker (AWS) + EBS | Same-AZ reattach; recovery ~**6.3 min** |
| Ingress SPOF → HA | Single replica SPOF; then 2 replicas + PDB |
| EBS snapshot restore | Ready ~**72s**; PVC→Running ~**15s**; cross-ns restore failed until same-ns VSC |
| HPA load | VMware **2→4**; AWS **2→3** |
| RBAC / PSA denials | Lab experiments Section 22 |
| Grafana OOM (historical) | Limits raised via GitOps |

**Lab measurements, not production SLAs.**

---

## Measured Results

| Metric | Lab value |
|---|---|
| Pod recreation | ~10s |
| Argo selfHeal | ~6s |
| Namespace recovery | ~23s |
| Snapshot Ready | ~72s |
| Snapshot restore PVC→Running | ~15s |
| AWS worker/EBS recovery | ~6.3 min |

---

## Known Limitations

Scope boundaries / future production work — not hidden failures:

- AWS `platform-observability-aws`: **Synced/Degraded** at portfolio freeze — Grafana surge Pod **Pending** (`Too many pods` on 2×t3.medium); **1/1 Ready Grafana still serves**; ProgressDeadlineExceeded on new ReplicaSet. **Known final-state limitation.**
- AWS NetworkPolicy enforcement not observed with current VPC CNI lab setup (objects exist).
- VMware control-plane scrape endpoints may be locally bound (non-app noise).
- Windows Ansible CLI blocked; Linux/Jenkins is the execution path.
- Live Boto3 on Windows workstation not fully exercised.
- AWS Backup EKS restore **not executed**; full EKS rebuild **not** destructively tested.
- EBS is **AZ-scoped**; cross-region DR not implemented.
- No centralized alerting/on-call; no production secret manager; Terraform state is local.

Details: [docs/portfolio/known-limitations.md](docs/portfolio/known-limitations.md)

---

## Repository Structure

```text
app/           FastAPI application
automation/    Python + Ansible
jenkins/       CI/CD
kubernetes/    workloads, overlays, GitOps apps
terraform/     AWS infrastructure
docs/          architecture, ADRs, ops, runbooks, portfolio
```

---

## Documentation Map

| Topic | Link |
|---|---|
| Architecture | [docs/architecture/project1-reference-architecture.md](docs/architecture/project1-reference-architecture.md) |
| ADRs | [docs/adr/README.md](docs/adr/README.md) |
| GitOps / Argo | [docs/argo-advanced-patterns.md](docs/argo-advanced-patterns.md) |
| Automation | [docs/automation/platform-automation-master-guide.md](docs/automation/platform-automation-master-guide.md) |
| Security | [docs/security-rbac.md](docs/security-rbac.md) |
| Storage | [docs/aws-storage-resilience.md](docs/aws-storage-resilience.md) |
| Observability | [docs/architecture/observability.md](docs/architecture/observability.md) |
| Reliability | [docs/architecture/reliability.md](docs/architecture/reliability.md) |
| DR | [docs/disaster-recovery-master-guide.md](docs/disaster-recovery-master-guide.md) |
| Operations | [docs/operations/README.md](docs/operations/README.md) |
| Interview | [docs/project1-interview-master-guide.md](docs/project1-interview-master-guide.md) |
| Portfolio | [docs/portfolio/README.md](docs/portfolio/README.md) |
| Full index | [docs/README.md](docs/README.md) |

---

## How to Explore (safe)

```bash
git clone https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git
cd kubernetes-platform-engineering-gitops
# Read docs/architecture/project1-reference-architecture.md

cd automation/python
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e ".[dev]"
platform-automate doctor
platform-automate platform verify
platform-automate ops health    # needs cluster kubeconfig
```

- **AWS lab execution** requires AWS access / EKS kubeconfig.  
- **Ansible** requires Linux (or Jenkins agent).  
- Basic repo exploration does **not** require AWS credentials.

---

## Interview Talking Points

1. Why Jenkins builds but Argo deploys (Git as desired state).  
2. Tag vs digest promotion (`0.1.4` digest pin).  
3. VMware MetalLB/ingress vs AWS ALB IP mode.  
4. EBS AZ topology and ~6.3 min worker recovery.  
5. Failure engineering: readiness ≠ running; Git rollback over `kubectl rollout undo`.  
6. Honest limitations (NetworkPolicy on AWS, pod density, DR scope).

Cheat sheet: [docs/portfolio/project1-interview-cheat-sheet.md](docs/portfolio/project1-interview-cheat-sheet.md)

---

## Author

Portfolio project by **Kiran** — Platform Engineering / Kubernetes / GitOps lab evidence in this repository.
