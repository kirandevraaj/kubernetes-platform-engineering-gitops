# Project 1 summary

**Title:** Kubernetes Platform Engineering & GitOps Lab  
**Type:** Portfolio / lab platform (not production customer deployment)

**Purpose:** Demonstrate end-to-end platform engineering across VMware and AWS EKS: IaC, CI, GitOps, observability, security, reliability testing, storage, DR, automation, and operations documentation.

**Tagline:** End-to-end Kubernetes platform engineering lab across VMware and AWS EKS with Terraform, Jenkins, Argo CD, observability, security, reliability testing, disaster recovery, and Python/Ansible automation.

**App:** `platform-lab` **0.1.4** @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

**Repo:** https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops  
**Image:** https://hub.docker.com/r/kirandevraaj/platform-lab

**Key experiments:** Pod/readiness/rollout failures, Argo selfHeal, worker+EBS recovery, ingress SPOF→HA, snapshots, RBAC/PSA, HPA load tests.

**Limitations:** See [known-limitations.md](./known-limitations.md) — including AWS observability Degraded (Grafana surge Pending under pod density) with Ready Grafana still serving.
