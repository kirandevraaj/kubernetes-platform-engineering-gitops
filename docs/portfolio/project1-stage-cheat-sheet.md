# Project 1 — Stage Cheat Sheet

One line per stage. Full detail: [project1-revisit-guide.md](./project1-revisit-guide.md). Environment history: [project1-environment-map.md](./project1-environment-map.md).

Environment key: **V** = VMware `ckad-lab` (historical full platform; now basic lab) · **A** = AWS EKS (historical runtime; destroyed) · **D** = docs only.

| # | Stage | One-line objective | Top technologies | Env | Primary document | One key lesson |
|---|---|---|---|---|---|---|
| 1 | Foundation | Record the existing kubeadm cluster and set environment rules | kubeadm, containerd, Calico, CoreDNS | V | [architecture-overview.md](../architecture/architecture-overview.md) | Confirm the kubectl context before any write |
| 2 | FastAPI + Docker | Build a small FastAPI workload and publish a non-root image | Python, FastAPI, Docker, Docker Hub | — | [app/README.md](../../app/README.md) | The tag names a release; the digest identifies the artifact |
| 3 | Kustomize packaging | Package once (base) and vary per environment (overlays) | Kubernetes, Kustomize | V | [architecture-overview.md](../architecture/architecture-overview.md) | One base, small overlays, no copy-paste manifests |
| 4 | Jenkins CI | Run test → build → push on a Linux agent | Jenkins, Docker Desktop | — | [jenkins/README.md](../../jenkins/README.md) | Publishing an image is not deploying it |
| 5 | Argo CD GitOps | Make Git the desired state for `platform-lab` on VMware | Argo CD v3.5.3 | V | [gitops/README.md](../../gitops/README.md) | selfHeal makes manual cluster edits temporary |
| 6 | CI → GitOps promotion | Jenkins commits the new version into the overlay; Argo deploys it | Jenkins, Git, Argo CD | V | [ci-cd-flow.md](../architecture/ci-cd-flow.md) | Overlay-only commits skip app CI (loop prevention) |
| 7 | Ingress, NetworkPolicy, MetalLB | Give the app an external entry point and restrict pod ingress | ingress-nginx, MetalLB L2, NetworkPolicy | V | [networking.md](../architecture/networking.md) | MetalLB answers ARP for a VIP; it is not a cloud LB |
| 8 | Prometheus / Grafana | Scrape `/metrics` and show a GitOps-managed dashboard | kube-prometheus-stack | V | [observability.md](../architecture/observability.md) | Size observability; Grafana OOM was fixed via Git |
| 9 | Reliability primitives | Add HPA, PDB, safe RollingUpdate, topology spread | HPA, PDB | V | [reliability.md](../architecture/reliability.md) | A PDB does not protect against involuntary failure |
| 10 | Terraform EKS | Build AWS VPC, EKS, IAM, LBC, Argo bootstrap as code | Terraform, EKS, ALB | A | [terraform/aws/README.md](../../terraform/aws/README.md) | Terraform and Argo must not own the same objects |
| 11 | Multi-env digest promotion | Promote one digest to both overlays | Jenkins, Kustomize `digest` | V+A | [ci-cd-flow.md](../architecture/ci-cd-flow.md) | Same digest everywhere = precise rollback |
| 12 | AWS capacity, observability, HPA | Size nodes, add light Prometheus/Grafana, load-test HPA | t3.medium, Prometheus, HPA | A | [aws-observability-capacity-analysis.md](../aws-observability-capacity-analysis.md) | Pod density (ENI), not CPU, limits small nodes |
| 13 | KSM, node-exporter, SRE dashboards | Add object/node metrics and 30-second platform dashboards | KSM, node-exporter, Grafana | V+A | [kubernetes-platform-observability.md](../kubernetes-platform-observability.md) | Metrics Server drives HPA; Prometheus does not |
| 14 | Self-healing and readiness | Prove ReplicaSet healing, Argo selfHeal, readiness removal | Deployment, probes, Argo | V | [vmware-pod-self-healing.md](../vmware-pod-self-healing.md) | Running is not Ready |
| 15 | Failed rollout + Git rollback | Ship a bad 0.1.5, watch the stall, roll back via Git | RollingUpdate, Argo, digests | V | [vmware-rollout-failure-rollback.md](../vmware-rollout-failure-rollback.md) | Readiness + `maxUnavailable: 0` keep old pods serving |
| 16 | Worker node failure | Stop a kubelet and observe NotReady behaviour | kubelet, taints, PDB | V | [vmware-node-failure-resilience.md](../vmware-node-failure-resilience.md) | Node failure waits ~300s before pods are evicted |
| 17 | Networking anatomy + ingress HA | Find why traffic failed, then remove the ingress SPOF | Calico, kube-proxy, MetalLB, ingress-nginx | V | [vmware-ingress-ha.md](../vmware-ingress-ha.md) | App HA is not external HA |
| 18 | local-path storage | StorageClass → PVC → PV → Pod, data survives pod delete | local-path, StatefulSet | V | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) | Same PVC API does not mean portable storage |
| 19 | EBS + node/AZ resilience | EBS CSI persistence and worker termination recovery | EBS CSI, gp3, EKS | A | [aws-storage-resilience.md](../aws-storage-resilience.md) | EBS is AZ-scoped; recovery ~6.3 min |
| 20 | Security / RBAC | Least-privilege SAs, RBAC matrix, PSA, NetworkPolicy | RBAC, PSA, Calico | V+A | [security-rbac.md](../security-rbac.md) | A RoleBinding scopes even a ClusterRole to one namespace |
| 21 | Advanced Argo CD | AppProjects, ApplicationSets, App-of-Apps, hooks, waves | Argo CD | V | [argo-advanced-patterns.md](../argo-advanced-patterns.md) | ApplicationSet generates Apps; App-of-Apps composes them |
| 22 | Python / Ansible automation | Guarded CLI for API work; Ansible for host config | Python, Boto3, Ansible | V (lab ns) | [platform-automation-master-guide.md](../automation/platform-automation-master-guide.md) | Don't build a second reconciler that fights Argo |
| 23 | Disaster recovery | Measure Git/Argo/namespace and EBS snapshot recovery | CSI snapshots, Git, Terraform | V+A | [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md) | Backup is not DR; restore returns to the snapshot point |
| 24 | Operations | Handbook, triage, runbooks, postmortems | Runbooks | D | [platform-operations-handbook.md](../operations/platform-operations-handbook.md) | Evidence before mutation |
| 25 | Portfolio packaging | ADRs, reference architecture, portfolio docs | ADRs, SVG | D | [project1-reference-architecture.md](../architecture/project1-reference-architecture.md) | Label Observed vs Designed honestly |
| 26 | Teardown + cleanup | Destroy AWS runtime; reduce VMware to a basic lab | Terraform destroy, kubectl, Helm | V+A | [vmware-lab-cleanup.md](../operations/vmware-lab-cleanup.md) | Clean the runtime, keep the source |

## Numbers worth remembering (lab, not SLAs)

| Measurement | Value | Source |
|---|---|---|
| Pod delete → replacement Ready (VMware) | ~10.4 s | [vmware-pod-self-healing.md](../vmware-pod-self-healing.md) |
| Argo selfHeal (label drift, VMware) | OutOfSync ~0.22 s → Synced ~0.96 s | [vmware-argo-self-healing.md](../vmware-argo-self-healing.md) |
| Argo selfHeal (DR drill, VMware) | ~6 s | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Worker kubelet stop → node Ready `Unknown` | ~42.7 s | [vmware-node-failure-resilience.md](../vmware-node-failure-resilience.md) |
| Ingress HA under worker loss | `/health` 75 OK / 0 FAIL (each worker) | [vmware-ingress-ha.md](../vmware-ingress-ha.md) |
| AWS HPA load test | 2 → 3 replicas ~65 s after load start | [aws-hpa-observability-load-test.md](../aws-hpa-observability-load-test.md) |
| AWS worker terminate → EBS pod Ready | ≈379 s (~6.3 min) | [aws-storage-resilience.md](../aws-storage-resilience.md) |
| EBS snapshot ReadyToUse | ~72 s | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Snapshot restore PVC → Running | ~15 s | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Namespace delete → recovered | ≈23 s | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Pod slots per node | t3.small 11 → t3.medium 17 | [aws-observability-capacity-analysis.md](../aws-observability-capacity-analysis.md) |
