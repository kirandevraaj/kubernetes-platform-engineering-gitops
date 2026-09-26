# ADR 002: EKS managed control plane

- **Status:** Accepted

## Context

VMware lab uses kubeadm (operator-owned control plane). AWS needs a cloud control plane with less CP ops burden for the lab.

## Decision

Use **Amazon EKS managed control plane** for AWS (`platform-lab-aws-lab-eks`).

## Comparison (conceptual)

| | VMware kubeadm | EKS |
|---|---|---|
| Control plane ownership | Operator VMs | AWS managed |
| Patching CP | Operator | AWS shared responsibility |
| HA CP | Lab single-ctrl design | AWS managed HA |
| Worker ops | Operator | Managed node groups |

## Consequences

Workers, add-ons, networking, and apps remain operator responsibilities. EKS does not replace GitOps or app runbooks.

## Evidence

Terraform EKS module · K8s **1.36.4** observed.
