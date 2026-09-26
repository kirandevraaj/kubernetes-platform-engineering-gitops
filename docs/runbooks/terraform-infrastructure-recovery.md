# Terraform Infrastructure Recovery Runbook (Project 1 — Section 25)

**Root module:** [`terraform/aws`](../../terraform/aws)  
**Backend today:** **Local state** (default); files **gitignored** — never commit `terraform.tfstate`, `terraform.tfvars`, or plans with secrets.  
**Canonical apply workspace:** `platform-aws-tools` container (Terraform may be absent from Windows PATH — see [`toolchain-inventory.md`](../toolchain-inventory.md)).  
**Critical rule:** **`terraform destroy` is not normal DR.** It is controlled teardown ([`terraform/aws/README.md`](../../terraform/aws/README.md)). DR **rebuilds forward** from code.

---

## Trigger Conditions

- `terraform plan` fails due to missing or corrupt state.
- Workstation loss with no state backup but AWS resources still running.
- VPC, EKS cluster, or node groups accidentally deleted.
- Need greenfield recovery in same or new region (documented model only for region — **not tested**).
- Drift between AWS reality and Git Terraform code after manual console changes.

---

## Severity Classification

| Level | Situation | Approach |
|-------|-----------|----------|
| **Low** | State OK; minor drift | `plan` → fix code or AWS → `apply` |
| **Medium** | State lost; AWS intact | Stop writes; backup inventory; import or greenfield |
| **High** | Cluster/VPC gone | Full rebuild sequence — [`terraform-recovery-runbook.md`](../terraform-recovery-runbook.md) |
| **Critical** | Code and state lost | Recover code from GitHub; state from backup or re-import |

---

## State

### What state contains

Mapping of Terraform addresses → AWS IDs (VPC `vpc-00c54a2d05f84fed6`, cluster `platform-lab-aws-lab-eks`, IAM roles, Helm releases, etc.). Required for **incremental** apply/destroy safety.

### What state does not replace

- Kubernetes application manifests (Argo / `kubernetes/overlays/aws`)
- EBS volume **data** (`vol-05faa26874d720ecd`)
- Git history

### Current lab posture

- Local backend per [`terraform/aws/versions.tf`](../../terraform/aws/versions.tf).
- Remote S3 + DynamoDB lock: **design only** — [`terraform-dr.md`](../terraform-dr.md).

---

## Backup (interim — until remote backend)

After every **successful** `apply`:

1. Copy `terraform.tfstate` and `terraform.tfstate.backup` to encrypted storage outside the repo.
2. Record: operator, UTC time, Git commit SHA of `terraform/aws`.
3. Never email state unencrypted; treat as sensitive (may embed attributes).

**Drill status:** **TBD** — recovery from copied state not yet measured.

---

## Plan

Always run read-only review before apply in recovery:

```bash
cd /workspace/terraform/aws   # platform-aws-tools
terraform fmt -check
terraform validate
terraform init
terraform plan -out=tfplan.recovery   # keep tfplan local; do not commit
```

**Expectations:**

- After state restore: plan should show **no or minimal** changes if AWS unchanged.
- After state loss: plan may propose **duplicate** resources — **do not apply blindly**.

Review plan for: EKS replacement, node group recreation, unintended destroy actions.

---

## Review

Human checklist before `apply`:

| Question | Action if NO |
|----------|--------------|
| Is this forward rebuild or import path documented? | Stop; choose strategy in [`terraform-dr.md`](../terraform-dr.md) |
| Does plan destroy production ALB/Ingress dependencies? | Run pre-destroy cleanup only for **intentional** teardown — not DR |
| Are Argo apps paused if needed? | Coordinate GitOps |
| Is state backup from T-1 available? | Copy before apply |
| Will EBS lab volume be touched? | Remove any resource targeting `vol-05faa26874d720ecd` from scope |

---

## Apply

1. `terraform apply tfplan.recovery` (or approved plan).
2. Wait for EKS ACTIVE, node group Ready, add-ons (EBS CSI, etc.).
3. Verify Helm releases: AWS Load Balancer Controller, metrics-server, Argo CD.
4. GitOps bootstrap: AppProject + Application for AWS overlay.

**Never** run `terraform destroy` as step 1 of DR.

---

## Verification

| Layer | Verify |
|-------|--------|
| AWS | VPC, subnets, NAT, EKS cluster name, node group instances |
| EKS add-ons | `aws-ebs-csi-driver`, core add-ons |
| Access | `aws eks update-kubeconfig`; API reachable; auth mode `API_AND_CONFIG_MAP` |
| Argo | Pods Ready; fetch repo; Applications Synced |
| Apps | `platform-lab-aws`, `platform-storage-aws`, observability |
| Storage | PVC `data-storage-demo-0` Bound (if cluster restored **with** existing PV/volume — otherwise snapshot path) |

Record apply duration for future **OBSERVED** RTO — currently **TBD** for full rebuild.

---

## Recovery Scenarios (quick reference)

### State restored from backup

1. Place files in `terraform/aws`.
2. `terraform init` → `plan` → minimal drift apply.

**Observed:** **TBD**

### State lost; AWS running

1. Stop Terraform applies.
2. Inventory IDs (VPC, cluster, volumes — see [`terraform-dr.md`](../terraform-dr.md)).
3. Choose **import** vs **parallel greenfield stack** + cutover.

**Observed:** **TBD** — **not safe** to experiment on live lab without approval.

### Code lost

Clone GitHub; match branch/SHA; init/plan. Git is SoT for **code**.

### Both code and state lost

Rebuild from GitHub + new AWS provisioning — full RTO **TBD**.

---

## Ownership Boundaries

| Layer | Owner |
|-------|--------|
| VPC, EKS, IAM, LB controller, Argo install | Terraform |
| App Deployments, Ingress app config | Argo + `kubernetes/overlays/aws` |
| EBS data | Snapshots / CSI — not Terraform state |
| Jenkins | Compose on workstation; Jenkinsfile in Git |

---

## Related

- [`../terraform-dr.md`](../terraform-dr.md)
- [`../terraform-recovery-runbook.md`](../terraform-recovery-runbook.md)
- [`aws-eks-disaster-recovery.md`](./aws-eks-disaster-recovery.md)
- Diagram: [`../diagrams/dr-dependency-graph.svg`](../diagrams/dr-dependency-graph.svg)
