# ADR 001: Terraform for AWS infrastructure

- **Status:** Accepted
- **Date:** 2026-09

## Context

AWS lab needs repeatable VPC, subnets, NAT, EKS, node groups, IAM, and add-ons.

## Decision

Use **Terraform** as the infrastructure lifecycle tool for the AWS platform under `terraform/`.

## Alternatives

| Option | Why not chosen for Project 1 |
|---|---|
| AWS CLI scripts | Harder drift control / review |
| CloudFormation | Viable; team chose Terraform familiarity |
| Manual console | Not reproducible |

## Consequences

- Plan → review → apply saved plan is the safety pattern.
- Local Terraform state is a **production gap** (remote backend not implemented).
- Terraform does **not** manage application runtime GitOps state.

## Evidence

`terraform/` · commit `5e304cd` · [terraform-apply-safety.md](../runbooks/terraform-apply-safety.md)
