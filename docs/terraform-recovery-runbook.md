# Terraform Recovery Runbook — AWS Platform Rebuild (Project 1 — Section 25)

**Purpose:** Conceptual **forward rebuild** sequence for the AWS lab after large-scale loss (new account, deleted VPC, deleted cluster, or deliberate greenfield recovery).  
**Not in scope:** Using **`terraform destroy`** as a routine DR technique — destroy is **controlled teardown**, documented separately in [`terraform/aws/README.md`](../terraform/aws/README.md) with pre-destroy Ingress/Application cleanup.

**Assumptions:**

- GitHub repository remains available (manifests, Terraform, GitOps YAML).
- Operator has AWS credentials with rights to create VPC/EKS/IAM/ELB (lab admin level).
- Work runs from **`platform-aws-tools`** (or equivalent) with Terraform installed in that workspace.
- **Timings:** Every phase duration is **TBD** unless measured in a future drill; the only **OBSERVED** recovery interval in Project 1 is **same-AZ StatefulSet pod Ready ≈ 6.3 minutes** after worker terminate ([`aws-storage-resilience.md`](./aws-storage-resilience.md)), which is **not** the same as full platform rebuild.

---

## 1. When to use this runbook

| Situation | Use this runbook? |
|-----------|-------------------|
| Argo app OutOfSync / bad manifest | No — fix Git, sync Argo |
| Single pod crash | No — Kubernetes self-healing |
| Worker node loss (EKS MNG replaces node) | Partial — verify GitOps; storage may need same-AZ capacity |
| Lost `terraform.tfstate` with live AWS | Partial — see [`terraform-dr.md`](./terraform-dr.md) import vs greenfield |
| VPC or cluster deleted; must stand up platform again | **Yes** |
| Region-wide AWS impairment | **Yes** (may require new region + overlay changes — **TBD**) |

---

## 2. Dependency graph (high level)

```text
AWS Account + IAM principal
        │
        ▼
   VPC + IGW + subnets (public/private)
        │
        ├──► NAT gateway (+ EIP) ──► private subnet egress for nodes
        │
        ▼
   IAM roles (EKS cluster, nodes, Pod Identity for LB controller / EBS CSI)
        │
        ▼
   EKS cluster (platform-lab-aws-lab-eks) + security groups
        │
        ├──► Managed node group (private subnets)
        ├──► EKS add-ons: vpc-cni, kube-proxy, coredns, pod-identity-agent
        ├──► (Lab) aws-ebs-csi-driver + Pod Identity for EBS lab
        │
        ▼
   Helm: AWS Load Balancer Controller
        │
        ▼
   Helm: Metrics Server
        │
        ▼
   Helm: Argo CD
        │
        ▼
   GitOps bootstrap: AppProject + Application(s) → kubernetes/overlays/aws
        │
        ▼
   Argo sync: platform-lab-aws, storage-lab apps, security-lab, observability (if enabled on AWS)
        │
        ▼
   Validate: Ingress → ALB, app health, storage-demo PVC bind, observability scrape
```

**Hard dependencies:**

- Private workers need **NAT** (lab default: single NAT in public AZ-a) before pulling images and reaching GitHub/Docker Hub.
- **Pod Identity / IAM** must exist before LB controller and EBS CSI can function.
- **Argo CD** must reach Git over HTTPS from nodes (NAT path).
- **EBS volumes are AZ-scoped** — rebuild in a new AZ layout may require new PVCs or snapshot restore (**TBD**).

---

## 3. Phase-by-phase procedure (conceptual)

Each phase ends with **verification gates**. Record start/end timestamps during drills to populate OBSERVED durations later.

### Phase 0 — Preconditions

| Step | Action | Gate |
|------|--------|------|
| 0.1 | Confirm Git ref (branch/tag) for recovery | Known commit SHA recorded |
| 0.2 | Confirm image availability: `kirandevraaj/platform-lab:0.1.4` @ documented digest | Pull succeeds from cluster network |
| 0.3 | Confirm `terraform.tfvars` exists locally (not in Git) with `cluster_endpoint_public_access_cidrs` | Plan does not prompt missing vars |
| 0.4 | If recovering state: restore or migrate state per [`terraform-dr.md`](./terraform-dr.md) | `terraform plan` sane |

**Duration:** **TBD**

### Phase 1 — AWS account and IAM

| Step | Action | Gate |
|------|--------|------|
| 1.1 | `aws sts get-caller-identity` | Expected account |
| 1.2 | Ensure human/CI role can create VPC, EKS, IAM, ELB | Policy check (document role name in private run log — not in Git) |

Terraform module [`modules/iam`](../terraform/aws/modules/iam) creates project-scoped roles — not reused admin roles.

**Duration:** **TBD**

### Phase 2 — Network (VPC)

| Step | Action | Gate |
|------|--------|------|
| 2.1 | `terraform apply` through VPC module | VPC CIDR `10.50.0.0/16`, public/private subnets in `ap-south-1a/b` |
| 2.2 | Verify IGW, route tables, NAT | Private subnet route to NAT; no accidental default VPC use |

**Prior lab VPC ID (for reference only if importing):** `vpc-00c54a2d05f84fed6`

**Duration:** **TBD**

### Phase 3 — EKS cluster and node group

| Step | Action | Gate |
|------|--------|------|
| 3.1 | Apply EKS cluster resource | `describe-cluster` status ACTIVE, version **1.36.x** |
| 3.2 | Confirm `authentication_mode` = **API_AND_CONFIG_MAP** (matches [`modules/eks/main.tf`](../terraform/aws/modules/eks/main.tf)) | Access entries / aws-auth map documented for operators |
| 3.3 | Apply managed node group | Nodes Ready |
| 3.4 | Apply core add-ons | `kubectl get pods -n kube-system` healthy |

**Duration:** **TBD**

### Phase 4 — Platform add-ons (Terraform Helm)

| Step | Action | Gate |
|------|--------|------|
| 4.1 | AWS Load Balancer Controller + Pod Identity | Controller pods running |
| 4.2 | Metrics Server | `kubectl top nodes` works |
| 4.3 | EBS CSI driver (storage lab) | `csidrivers` includes `ebs.csi.aws.com`; StorageClass `ebs-gp3` |

**Duration:** **TBD**

### Phase 5 — Argo CD and GitOps bootstrap

| Step | Action | Gate |
|------|--------|------|
| 5.1 | Helm install Argo CD (namespace `argocd`) | Server/deployment healthy |
| 5.2 | Bootstrap AppProject + Application for `platform-lab-aws` | `kubectl get applications -n argocd` |
| 5.3 | Register additional Applications (storage, security) if not in bootstrap | Synced / Healthy |

Bootstrap is **temporary Terraform ownership** — long-term desired state remains in Git under `gitops/` mirrors and `kubernetes/overlays/aws`.

**Duration:** **TBD**

### Phase 6 — Application and observability validation

| Step | Action | Gate |
|------|--------|------|
| 6.1 | Argo sync `platform-lab-aws` | Deployment 2/2, image digest matches promotion |
| 6.2 | Ingress creates ALB | `kubectl get ingress -n platform-lab` ADDRESS/hostname |
| 6.3 | HTTP check via ALB DNS | `/` returns expected version/env |
| 6.4 | Storage lab: StatefulSet `storage-demo`, PVC bound | **New** volume unless snapshot restore executed |
| 6.5 | Observability on AWS (if deployed) | Prometheus/Grafana targets **TBD** for AWS path |

**Duration:** **TBD**

### Phase 7 — Data recovery (optional branch)

| Scenario | Path | Status |
|----------|------|--------|
| Reattach existing EBS `vol-05faa26874d720ecd` | Only if volume survived and AZ/node topology matches | **TBD** drill |
| Restore from EBS snapshot | EC2 API or CSI restore workflow | **TBD** — no lab snapshots at inventory |
| AWS Backup EKS restore | See [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) | **Not configured** at inventory |

---

## 4. Parallel paths and anti-patterns

| Anti-pattern | Why |
|--------------|-----|
| `kubectl apply` production overlays bypassing Argo | Breaks GitOps audit trail during recovery |
| `terraform destroy` to “fix” DR | Deletes infrastructure by design; use forward rebuild or targeted resource fix |
| Applying VMware overlays to EKS | Separate contexts: `ckad-lab` vs `platform-lab-aws` |
| Committing secrets into emergency “hotfix” YAML | Use External Secrets / SSM patterns in real systems; lab uses private tfvars |

---

## 5. Rollback strategy (conceptual)

| Failure point | Rollback idea |
|---------------|---------------|
| Bad Terraform apply | Restore state version + reverse commit; or targeted `terraform apply` with fixed code |
| Bad GitOps commit | `git revert` + Argo sync |
| Partial cluster | Do not destroy blindly — isolate broken add-on, reinstall Helm release |

**OBSERVED rollback drill:** **TBD**

---

## 6. VMware lab (out of Terraform scope)

VMware **`ckad-lab`** recovery is **not** driven by `terraform/aws`. A separate runbook would cover:

- VM snapshots / host restore (hypervisor-level — outside repo)
- kubeadm/etcd backup (**not implemented in Project 1**)
- Reinstall Argo CD and re-sync Applications

**Status:** **TBD** — AWS runbook above does not substitute for VMware control-plane DR.

---

## 7. Evidence to capture during drills

| Artifact | Reason |
|----------|--------|
| Git commit SHA | Code version |
| Terraform plan/apply output (sanitized) | Infra version |
| `kubectl get applications -A` | GitOps health |
| ALB DNS name | External entry |
| EBS volume IDs / PVC bindings | Data continuity |
| Start/end UTC timestamps | Populate RTO |

Store evidence outside Git if it contains account-specific hostnames.

---

## 8. Related

- [`terraform-dr.md`](./terraform-dr.md)
- [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md)
- [`business-continuity.md`](./business-continuity.md)
- [`terraform/aws/README.md`](../terraform/aws/README.md)
