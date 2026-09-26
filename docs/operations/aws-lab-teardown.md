# AWS lab teardown record

**Date:** 2026-09-26  
**Region:** ap-south-1  
**Account:** 202191872326  
**Identity:** `arn:aws:iam::202191872326:user/kiran-admin`  
**Git HEAD at teardown:** `7c8e84d` (portfolio freeze; this doc may be a follow-up commit)

## Destroyed (Project 1)

| Resource | ID / name |
|---|---|
| EKS cluster | `platform-lab-aws-lab-eks` |
| Node group | `platform-lab-aws-lab-managed` |
| VPC | `vpc-00c54a2d05f84fed6` (`10.50.0.0/16`) |
| NAT Gateway | `nat-0e806d57d28b97ffb` |
| EIP | `eipalloc-08b1ff7d544ff9e6a` |
| ALB | `k8s-platform-platform-4c216154e7` (orphaned after LB controller remove; deleted to unblock VPC) |
| Project target group | `k8s-platform-platform-c5c674fffb` |
| Project ALB security groups | `sg-07b857417f547b8e5`, `sg-0cadb323396429d75` |
| Project EBS (PVC) | `vol-05faa26874d720ecd` (available after cluster gone; deleted — CSI/PVC ownership unambiguous) |
| Terraform-managed IAM roles/policies | EKS cluster/node, EBS CSI, AWS LBC |
| Helm: Argo CD, metrics-server, AWS LBC | Destroyed via Terraform |
| EKS add-ons | vpc-cni, kube-proxy, coredns, pod-identity, ebs-csi, snapshot-controller |

## Preserved

| Item | Notes |
|---|---|
| AWS account | intact |
| IAM user `kiran-admin` | intact; STS still works |
| Default VPC | `vpc-03da1af16f74334f2` (`172.31.0.0/16`, IsDefault=true) |
| Unrelated TG `lab-web-tg` | VPC `vpc-070293e99a9537c75` — **not deleted** |
| GitHub / Docker Hub | unchanged |
| Terraform / Kubernetes / docs source | unchanged (recreatable) |
| VMware `ckad-lab` | verified intact after teardown |

## Method

1. `terraform plan -destroy -out=tfplan-destroy` (52 resources; safety gate passed)  
2. `terraform apply tfplan-destroy`  
3. `null_resource.destroy_safety` ran `pre-destroy-cleanup.sh` (Argo/Ingress cleanup; ALB wait timed out with 1 ALB remaining)  
4. Kubernetes force-clear of stuck Application/Ingress finalizers (same intended lifecycle)  
5. Orphaned Project ALB deleted after LB controller destroyed (ENI/subnet unblock)  
6. First apply left public subnets/IGW/VPC due to DependencyViolation  
7. Deleted leftover Project ALB SGs + Project TG + available Project EBS  
8. `terraform apply tfplan-destroy-remain` (4 resources) — VPC fully gone  

## Terraform after teardown

- `terraform state list` → **empty**  
- `terraform plan` → wants to **recreate** the full AWS lab from source (expected; environment recreatable)

## Cost note

Project 1 continuously running AWS infrastructure (EKS, workers, NAT, ALB, project EBS, project EIP) has been torn down. Billing may lag; unrelated account resources (e.g. `lab-web-tg`) may still incur charges. Self-owned EBS snapshots in `ap-south-1`: **0**.

## VMware post-check

Nodes Ready · `platform-lab` 2/2 · digest `0.1.4` @ `sha256:1cca2b…872ff` · `/health` 200 · storage/security/observability Argo Healthy.
