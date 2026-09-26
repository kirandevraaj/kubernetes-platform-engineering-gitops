# Terraform and Disaster Recovery (Project 1 — Section 25)

**Purpose:** Explain why Terraform **code** and Terraform **state** are different recovery assets, document risks of **local state** in this project, and define a target remote-backend posture without claiming it is already deployed.  
**Root module:** [`terraform/aws`](../terraform/aws)  
**Current posture:** **Local backend** (default); state files are **gitignored** and must not be committed.

---

## 1. Code ≠ state (core DR concept)

| Artifact | What it is | Recovery role |
|----------|------------|---------------|
| **`.tf` files** | Declared desired infrastructure | Re-run `init` / `plan` / `apply` to create or update resources |
| **State** (`terraform.tfstate`) | Mapping of resource addresses → real AWS IDs, dependencies, metadata | Lets Terraform perform **incremental** updates and destroys safely |
| **Plan output** | Ephemeral diff | Evidence for change review; not a substitute for state |

If AWS resources exist but state is **lost or stale**, Terraform may attempt to **create duplicates** (name collisions) or fail to **destroy** orphans. Recovery options include restoring state from backup, `terraform import` for known IDs, or controlled teardown outside Terraform (last resort).

**Project 1 example IDs you would need after state loss (non-secret inventory):**

| Resource | Known identifier (lab) |
|----------|-------------------------|
| VPC | `vpc-00c54a2d05f84fed6` |
| EKS cluster | `platform-lab-aws-lab-eks` |
| EBS lab volume | `vol-05faa26874d720ecd` |
| Region | `ap-south-1` |

Re-import is tedious; **preventing state loss** is cheaper than reconstructing it.

---

## 2. What this root module owns (recovery boundary)

From [`terraform/aws/README.md`](../terraform/aws/README.md):

```text
Terraform owns:
  VPC (10.50.0.0/16), NAT, IAM, EKS 1.36, managed node group,
  EKS add-ons, AWS Load Balancer Controller, Metrics Server, Argo CD (Helm),
  GitOps bootstrap (AppProject + Application)

Argo CD owns (after bootstrap):
  kubernetes/overlays/aws — Deployment, Service, Ingress, HPA, PDB, NetworkPolicy, …
```

**DR implication:** Rebuilding the **platform shell** is Terraform-shaped; rebuilding **application desired state** is Git + Argo-shaped. A single `terraform apply` does not replace a full GitOps re-sync if Argo data in etcd is gone—you reinstall Argo and re-point Applications at Git.

---

## 3. Local state: current lab choice

[`terraform/aws/versions.tf`](../terraform/aws/versions.tf) explicitly documents:

```hcl
# Local state for the initial lab stage. Remote (S3) backend comes later.
# State files are gitignored and must never be committed.
```

There is **no** `backend "s3"` block configured yet.

### 3.1 Risks of local state

| Risk | Consequence | Mitigation (target) |
|------|-------------|---------------------|
| Workstation disk failure | State file gone; Terraform blind to existing AWS spend | Remote backend + replication |
| No locking | Two operators `apply` concurrently → corrupt state | S3 + DynamoDB lock table (or Terraform Cloud) |
| No versioning | Cannot roll state back to pre-bad-apply | S3 versioning on state bucket |
| Backup ad hoc | Recovery depends on personal copies | Automated state backup policy |
| CI not authoritative | Applies run from `platform-aws-tools` container; state lives where that workspace mounts | Document canonical state location |

**OBSERVED:** Inventory script checks `/workspace/terraform/aws/*.tfstate*` inside the tools container — presence depends on where apply was run. **State backup drill: TBD.**

### 3.2 What local state does *not* mean

- Local state does **not** make AWS resources “local”—they remain in **`ap-south-1`**.
- Losing state does **not** automatically delete the VPC or EKS cluster.
- **`terraform destroy` is not DR** — it is intentional teardown. Normal DR rebuilds **forward** from Git/code, optionally into a **new** stack name/VPC.

---

## 4. Target remote backend (design — not applied)

When the project promotes state off the workstation, a typical AWS pattern:

| Component | Purpose |
|-----------|---------|
| S3 bucket | Store `terraform.tfstate` |
| Bucket versioning | Restore previous state object after mistake |
| SSE-KMS or SSE-S3 | Encrypt state at rest (state may contain sensitive attributes) |
| DynamoDB table | State locking |
| IAM policy | Least privilege for CI/human role that runs Terraform |
| Optional: separate bucket per environment | `aws-lab` vs future `prod` |

**Migration steps (conceptual — TBD in lab):**

1. Create bucket + lock table (often a small bootstrap stack or console one-time).
2. Add `backend "s3"` to `terraform` block with bucket/key/region/dynamodb_table.
3. `terraform init -migrate-state` from the canonical workspace (`platform-aws-tools`).
4. Verify `terraform plan` is empty/no-op.
5. Document who may run apply and where state must live.

---

## 5. State backup without remote backend (interim)

Until remote backend exists, treat state like a secret-adjacent artifact:

| Practice | Notes |
|----------|-------|
| Copy `terraform.tfstate` + `terraform.tfstate.backup` after every successful apply | Timestamped copies outside the repo |
| Store copies encrypted (OS vault, encrypted volume) | State can embed sensitive values |
| Never commit to Git | Enforced via `.gitignore` |
| Record apply operator + git commit SHA in run log | Correlates infra to code version |

**Interim recovery drill status:** **TBD**

---

## 6. Recovery scenarios

### 6.1 State file restored from backup

1. Place known-good `terraform.tfstate` in `terraform/aws`.
2. `terraform init`
3. `terraform plan` — expect minimal drift if AWS unchanged.
4. Reconcile drift carefully; prefer Git-driven fixes for Kubernetes app layer.

**OBSERVED duration:** **TBD**

### 6.2 State lost; AWS resources still running

1. Stop all Terraform writes until strategy chosen.
2. Inventory live AWS (VPC `vpc-00c54a2d05f84fed6`, cluster name, node groups, add-ons).
3. Either:
   - **Import path:** `terraform import` for each resource address (high effort), or
   - **Greenfield path:** Build parallel stack from code, cut over GitOps, retire old stack with controlled destroy after validation.

**OBSERVED:** **TBD** — do not practice on production accounts without approval.

### 6.3 Code lost; state exists

Unlikely if Git is source of truth. Recovery: clone GitHub repo, match ref, `terraform init`, `plan`. State without code is worse—**Git is the canonical code store** for this project.

### 6.4 Both lost

Rebuild from GitHub + re-provision AWS from [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md). RPO for infrastructure = last merged Terraform commit; RTO **TBD**.

---

## 7. Terraform vs GitOps vs Jenkins (DR ownership)

| Layer | Source of truth | Terraform role |
|-------|-----------------|----------------|
| VPC/EKS/IAM | `terraform/aws` | Full lifecycle |
| Argo CD install | Terraform Helm | Reinstall on new cluster |
| App manifests | `kubernetes/overlays/aws` | None (Argo) |
| Image digest/tag | Git (Jenkins promotion) | None |
| EBS data | EBS volume / snapshots | CSI driver infra may be Terraform; **data is not** |

---

## 8. Tooling notes (Section 24 inventory)

- Terraform may be **absent from Windows PATH**; lab applies are expected via **`platform-aws-tools`** container with AWS credentials configured (`aws sts get-caller-identity`).
- `terraform plan` alone does not create resources — useful for DR readiness review.

---

## 9. Related

- [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) — ordered rebuild
- [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md) — RPO/RTO table
- [`terraform/aws/README.md`](../terraform/aws/README.md) — modules, destroy safety
