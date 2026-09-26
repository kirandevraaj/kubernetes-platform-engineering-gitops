# Project 1 engineering narrative

**Problem:** Build a modern platform engineering practice that extends existing VMware/infrastructure skills into Kubernetes, AWS, GitOps, and automation — with measurable evidence.

**Architecture:** Dual environments — VMware kubeadm lab + AWS EKS — sharing application GitOps overlays and digest-pinned artifacts.

**Delivery:** Jenkins CI produces immutable images; Git stores desired state; Argo CD reconciles (separate control planes per cluster).

**Infrastructure:** Terraform manages AWS VPC/EKS/IAM/add-ons.

**Automation:** Python CLI for API orchestration; Ansible for operational config on Linux/Jenkins; clear boundaries vs Terraform and Argo.

**Observability:** Prometheus/Grafana/KSM/node-exporter/Metrics Server with environment-specific installs.

**Security:** RBAC, Pod Security, NetworkPolicy (enforcement differs by environment), IAM on AWS.

**Reliability:** HPA/PDB/topology plus controlled failure experiments and Git-based rollback.

**Storage:** local-path on VMware; EBS CSI + snapshots on AWS (AZ-aware).

**Recovery:** Git + Terraform + snapshots + runbooks; selected drills measured; full rebuild/AWS Backup restore not executed.

**Operations:** Handbook, runbooks, evidence bundles, postmortems.

This is capability progression, not a career biography.
