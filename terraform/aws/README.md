# Terraform — AWS platform foundation

Status: **configuration only**. This directory does **not** create AWS resources yet.

## Purpose

`terraform/aws` owns AWS infrastructure for the platform-lab AWS target:

```text
Terraform
  → VPC 10.50.0.0/16 (planned)
  → public + private subnets / IGW / single NAT (planned)
  → EKS 1.36 + managed node group (planned)
  → AWS load balancing (planned)
```

Application delivery stays with Jenkins + Docker Hub. Kubernetes desired state stays in Git (`kubernetes/overlays/aws`). Reconciliation will use Argo CD **inside** the AWS cluster later.

## Ownership

| Layer | Owner |
|---|---|
| AWS infrastructure | Terraform (this directory) |
| Container image | Jenkins → Docker Hub |
| Workload manifests | Git Kustomize overlays |
| Cluster reconcile | Argo CD (AWS, later) |

## Region and planned architecture

| Setting | Value |
|---|---|
| Region | `ap-south-1` (variable default) |
| VPC CIDR | `10.50.0.0/16` |
| AZs | `ap-south-1a`, `ap-south-1b` |
| Subnets | 2 public + 2 private |
| Workers | Private subnets |
| NAT | Single NAT Gateway (cost-conscious lab) |
| Kubernetes | EKS **1.36** |
| Registry (initial) | Docker Hub `kirandevraaj/platform-lab` |
| Observability on AWS | Deferred |

Do **not** reuse the account default VPC (`172.31.0.0/16`).

## Local state (initial lab phase)

- Backend is **local** (no S3 backend yet).
- `.terraform/` and `*.tfstate*` are gitignored.
- Never commit state or `terraform.tfvars`.

## Credentials

Use the standard AWS SDK chain from the `platform-aws-tools` container (shared config/credentials or env). Do not put keys in Terraform files.

## Current phase

This foundation defines providers, variables, locals, and outputs only. `main.tf` creates **zero** resources.

Later phases add VPC, then EKS, then node groups and load balancing, then Argo CD / overlay work outside Terraform as needed.

## Validate (from toolbox)

```bash
cd /workspace/terraform/aws
terraform fmt -check
terraform init
terraform validate
terraform state list   # expect empty
```

Do not run `terraform apply` until an explicit Step 10 phase authorizes it.
