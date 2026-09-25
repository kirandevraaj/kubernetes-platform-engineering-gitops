# Terraform — AWS platform (EKS + GitOps)

Status: **implemented, not applied**. This directory defines the full AWS platform.
`terraform plan` is allowed. **`terraform apply` / `destroy` require explicit approval.**

## Architecture

```text
Terraform (this root)
  → VPC 10.50.0.0/16 (2 public + 2 private, IGW, 1 NAT by default)
  → IAM (EKS cluster, node, AWS LB Controller Pod Identity)
  → EKS 1.36 + managed node group (private workers)
  → EKS add-ons (vpc-cni, kube-proxy, coredns, pod-identity-agent)
  → Helm: AWS Load Balancer Controller
  → Helm: Argo CD
  → Bootstrap: AppProject + Application → kubernetes/overlays/aws

Argo CD (inside EKS) owns:
  Deployment / Service / Ingress / HPA / PDB / NetworkPolicy / ConfigMap
```

Traffic path after apply:

```text
Internet → AWS ALB (created by AWS LB Controller from Ingress)
        → Service platform-lab :8000
        → Pods (private subnets, VPC CNI)
```

## Module structure

| Module | Path | Owns |
|---|---|---|
| VPC | `modules/vpc` | VPC, subnets, IGW, NAT/EIP, route tables |
| IAM | `modules/iam` | Cluster / node / LB Controller roles + policies |
| EKS | `modules/eks` | Cluster, managed node group, add-ons, SGs, launch template |
| AWS LB Controller | `modules/aws_load_balancer_controller` | Pod Identity association + Helm release |
| Argo CD | `modules/argocd` | Helm release in namespace `argocd` |
| GitOps bootstrap | `modules/gitops_bootstrap` | Temporary kubectl apply of AppProject/Application |

Single entry point: this directory (`terraform/aws`).

## Resource ownership

| Layer | Owner |
|---|---|
| AWS network + EKS + controller + Argo CD install | Terraform |
| Kubernetes application objects (`kubernetes/overlays/aws`) | Argo CD |
| Container image | Jenkins → Docker Hub |
| VMware local lab Argo CD apps | Untouched (separate cluster) |

Terraform and Argo CD must not manage the same application objects.

## Network design

| Setting | Default |
|---|---|
| Region | `ap-south-1` |
| VPC | `10.50.0.0/16` (dedicated; never the account default VPC) |
| Public | `10.50.0.0/20`, `10.50.16.0/20` |
| Private | `10.50.32.0/20`, `10.50.48.0/20` |
| NAT | One NAT in public AZ-a (`enable_single_nat_gateway=true`) |
| Workers | Private subnets only |

Set `enable_single_nat_gateway=false` later for one NAT per AZ without redesigning the module.

## EKS design

- Version **1.36** (standard support)
- API: private + public endpoints; public restricted by `cluster_endpoint_public_access_cidrs` (**no `0.0.0.0/0`**)
- Managed node group: default **t3.small**, desired 2 / min 1 / max 3
- Root volume: **20 GiB gp3**, encrypted, IMDSv2 required
- Add-ons: VPC CNI, kube-proxy, CoreDNS, eks-pod-identity-agent (versions from `most_recent` for the cluster version)
- EBS CSI: not installed (no PVC dependency in this lab)

## IAM design

Project-scoped roles only (no reuse of `ec2_admin_role` / AdministratorAccess):

- EKS cluster role + `AmazonEKSClusterPolicy` (+ VPC resource controller)
- Node role + WorkerNode / CNI / ECR read-only
- AWS Load Balancer Controller role via **EKS Pod Identity** + official controller IAM policy JSON

## ALB flow

```text
Ingress (ingressClassName: alb)
  → AWS Load Balancer Controller
  → internet-facing ALB + target group (target-type: ip)
  → pods
```

No hand-managed `aws_lb` resource. No MetalLB / ingress-nginx on AWS.

## Argo CD bootstrap

1. Terraform installs Argo CD with Helm into EKS.
2. `gitops_bootstrap` kubectl-applies AppProject `platform-lab-aws` and Application `platform-lab-aws`.
3. Application watches `kubernetes/overlays/aws` on `main`.
4. Mirror manifests live under `gitops/projects/platform-lab-aws.yaml` and `gitops/applications/platform-lab-aws.yaml` for documentation — **do not apply them to the VMware lab**.

Bootstrap is temporary: Terraform does not take long-term ownership of app manifests.

## Destroy ordering / safety

Critical path (implemented):

1. `null_resource.destroy_safety` destroy provisioner runs **first** (depends on Helm/bootstrap/EKS).
2. Script `scripts/pre-destroy-cleanup.sh` deletes Argo Applications and Ingresses while the API and LB Controller still exist.
3. GitOps bootstrap destroy deletes Application/AppProject (Argo finalizer prunes app resources).
4. Helm releases (Argo CD, LB Controller) uninstall.
5. Node group → EKS cluster → IAM/VPC (NAT, EIP, subnets, IGW, VPC).

This avoids stuck destroys from Ingress finalizers (`ingress.k8s.aws/resources`) after the cluster is gone.

## Cost drivers (fixed, approximate)

With the approved lab defaults (24×7): EKS control plane, 2× workers, 1 NAT + EIP IPv4, 1 ALB (from Ingress), 40 GiB gp3. See the separate cost-analysis canvas for current unit prices. Logging off by default (`enable_cluster_logging=false`).

## Variables (defaults = approved low-cost lab)

| Variable | Default |
|---|---|
| `aws_region` | `ap-south-1` |
| `environment` | `aws-lab` |
| `vpc_cidr` / subnet CIDRs / AZs | as approved |
| `kubernetes_version` | `1.36` |
| `node_instance_type` | `t3.small` |
| `desired/min/max_node_count` | `2` / `1` / `3` |
| `root_volume_size` | `20` |
| `enable_single_nat_gateway` | `true` |
| `cluster_endpoint_public_access` | `true` |
| `cluster_endpoint_public_access_cidrs` | **required** (your `/32`) |
| `enable_cluster_logging` | `false` |

Tags (provider default_tags):

- `Project = kubernetes-platform-engineering-gitops`
- `Environment = aws-lab` (from `var.environment`)
- `ManagedBy = terraform`

## Prerequisites

1. `platform-aws-tools` container running with AWS credentials configured (`aws sts get-caller-identity` works).
2. IAM principal can create VPC/EKS/IAM/ELB (lab admin for apply phase).
3. Copy `terraform.tfvars.example` → `terraform.tfvars` and set `cluster_endpoint_public_access_cidrs` to your public IP `/32`.
4. Do **not** commit `terraform.tfvars` or state files.

## Validate (no resources created by plan alone)

```bash
cd /workspace/terraform/aws
terraform fmt -recursive
terraform init
terraform validate
terraform plan -var="cluster_endpoint_public_access_cidrs=[\"YOUR.PUBLIC.IP/32\"]"
```

`terraform plan` does **not** create AWS resources.

## Apply procedure (future approval only)

```bash
terraform apply -var="cluster_endpoint_public_access_cidrs=[\"YOUR.PUBLIC.IP/32\"]"
aws eks update-kubeconfig --region ap-south-1 --name platform-lab-aws-lab-eks
kubectl -n argocd get applications
kubectl -n platform-lab get ingress
```

## Destroy procedure (future approval only)

```bash
terraform destroy -var="cluster_endpoint_public_access_cidrs=[\"YOUR.PUBLIC.IP/32\"]"
```

Prefer `terraform destroy` over Console cleanup. If a destroy sticks on ENIs/SGs, re-run destroy after the pre-destroy script has removed Ingress/ALBs; check for leftover ALBs tagged by the controller.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Plan asks for `cluster_endpoint_public_access_cidrs` | Required security variable — set your `/32` |
| Nodes never Ready | NAT/routing, CNI addon, or subnet tags |
| Ingress no ALB | LB Controller Pod Identity / IAM policy / subnet role tags |
| Destroy stuck on SG/ENI | Ingress finalizers — ensure destroy_safety ran; delete Ingress manually if needed while cluster lives |
| Argo app not syncing | Git path/branch, AppProject whitelist, DNS from nodes via NAT |

## Out of scope (intentionally)

RDS, DynamoDB, ElastiCache, OpenSearch, MSK, CloudFront, Route53 hosted zone, ACM, WAF, second NAT (unless `enable_single_nat_gateway=false`), hand-managed ALB, ECR (Docker Hub remains the image source for now).
