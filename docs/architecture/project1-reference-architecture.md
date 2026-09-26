# Project 1 Reference Architecture

**Status:** Implemented + Verified (lab) · **Environments:** VMware + AWS · **Last validated:** 2026-09-26  
**Primary diagram:** [project1-reference-architecture.svg](../diagrams/project1-reference-architecture.svg)

## 1. Executive Summary

Portfolio / lab platform spanning VMware kubeadm and AWS EKS with Terraform, Jenkins, Argo CD, immutable digests, observability, security, storage, DR drills, Python/Ansible automation, and operational runbooks.

## 2. Engineering Goals

Repeatable delivery, observable runtime, controlled failure learning, honest scope boundaries.

## 3. Architecture Principles

Git as desired state · CI ≠ CD · digest immutability · environment-appropriate ingress/storage · evidence before mutation · Observed ≠ Designed.

## 4. High-Level Architecture

See SVG. Control/management flow is separate from user data plane.

## 5. VMware Architecture

`ckad-lab` · K8s **1.31.14** · 3 nodes · Calico · MetalLB `192.168.56.200` · ingress-nginx HA · local-path · Argo **v3.5.3**.

## 6. AWS Architecture

EKS **1.36.4** · `ap-south-1` · 2×t3.medium · ALB IP targets · EBS CSI · Argo **v3.1.0** · single NAT (cost-conscious lab).

## 7–10. CI/CD · GitOps · IaC · Automation

Jenkins builds/promotes · Argo reconciles · Terraform owns AWS infra · Python/Ansible for ops automation (boundaries in [tool-boundaries.md](./tool-boundaries.md)).

## 11–15. Networking · Observability · Security · Storage · Reliability

See ADRs 006–009, 012–013 and linked experiment docs. HPA/PDB/topology validated; NetworkPolicy **Partial** on AWS.

## 16–17. DR · Operations

Section 25–26 guides and runbooks. Measured lab RTOs; not SLAs.

## 18–20. Ownership · Failure · Recovery domains

[ownership-boundaries.md](./ownership-boundaries.md) · failure-domain SVG · Git/Argo/EBS/TF recovery paths.

## 21–22. Data flow · Control flow

CI: Dev→GitHub→Jenkins→Hub→digest→GitOps. CD: Git→Argo→API. Runtime: Client→VIP/ALB→Pod. Metrics: `/metrics`→Prometheus→Grafana.

## 23–27. Decisions · Limitations · Gaps · Lessons · Portfolio

[adr/](../adr/) · [known-limitations.md](../portfolio/known-limitations.md) · [production-gaps.md](../operations/production-gaps.md) · [portfolio/README.md](../portfolio/README.md)

**Known freeze note:** AWS observability Application may be Synced/Degraded due to Grafana surge Pending under pod density — serving Grafana Ready ([aws-observability-degraded-final-state.md](../portfolio/aws-observability-degraded-final-state.md)).
