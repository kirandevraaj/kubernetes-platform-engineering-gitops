# AWS Backup and EKS Disaster Recovery (Project 1 — Section 25)

**Purpose:** Assess how **AWS Backup for Amazon EKS** fits this lab, what it would include/exclude per current AWS product concepts, prerequisites for this cluster’s auth mode, and the **inventory-time gap** (no EKS protected resources).  
**Cluster:** `platform-lab-aws-lab-eks` · region **`ap-south-1`** · Kubernetes **1.36.4** · VPC **`vpc-00c54a2d05f84fed6`**  
**Disclaimer:** AWS Backup behavior evolves; validate against [AWS Backup for EKS](https://docs.aws.amazon.com/aws-backup/latest/devguide/working-with-eks.html) before production decisions. This document is **lab assessment**, not a certified compliance statement.

---

## 1. What AWS Backup for EKS is (conceptual)

AWS Backup can treat an **EKS cluster** as a **protected resource** when enrolled in a **backup plan**. Backups capture **Kubernetes resource metadata** AWS Backup supports for EKS (cluster-scoped and namespaced objects per plan rules), stored in a **backup vault**, with **retention** and **lifecycle** policies.

It is **not** a replacement for:

- **Git** (desired state for GitOps workloads)
- **Container images** (Docker Hub / ECR)
- **All persistent volume data** unless separately protected (EBS snapshots, AWS Backup advanced policies, or application-level backup)
- **Terraform state** (not an EKS API object)

Think of AWS Backup for EKS as **API-object recovery** for supported Kubernetes kinds, plus AWS-orchestrated restore workflows—not full “clone my running system including every byte on disk” unless you design volume backup too.

---

## 2. Includes vs excludes (engineering view)

Tables below reflect **typical** AWS Backup for EKS scope as described in AWS documentation concepts. Exact resource kinds and restore behavior must be confirmed at enrollment time.

### 2.1 Generally in scope (when plan protects EKS cluster)

| Category | Examples relevant to Project 1 | Lab notes |
|----------|----------------------------------|-----------|
| Namespaced workloads (supported kinds) | Deployments, Services, ConfigMaps, Secrets (metadata in backup; **Secret values** still sensitive), Ingress, HPA, PDB, NetworkPolicy | `platform-lab`, `storage-lab`, `security-lab` objects **would be** candidates if plan exists |
| Cluster-scoped (supported kinds) | StorageClass, PersistentVolume, ClusterRole/Binding (if supported in plan) | `ebs-gp3`, PV `pvc-612d84fb-…` metadata |
| EKS cluster association | Cluster registered as protected resource | **Not enrolled** at inventory |

### 2.2 Out of scope or incomplete without extra work

| Category | Why it matters in this lab |
|----------|----------------------------|
| **EBS volume contents** | Lab data on `vol-05faa26874d720ecd` lives on block storage; EKS backup ≠ automatic byte-for-byte PVC restore unless EBS snapshot strategy exists |
| **Running pod state / emptyDir** | Ephemeral; rebuild from Deployment |
| **Argo CD helm release internals** | Reinstall Argo via Terraform/Helm; restore Git repo + Applications |
| **AWS infrastructure** | VPC, NAT, node groups, IAM — **Terraform**, not EKS backup |
| **Docker Hub image** | Pull by tag/digest from registry |
| **Unsupported CRDs / operators** | **VolumeSnapshot** CRDs absent at inventory — snapshot objects not in play |
| **Metrics/events not stored as K8s objects** | Observability data in Prometheus TSDB — separate backup model |

---

## 3. Prerequisites (auth mode and access)

EKS cluster access configuration for this lab (Terraform):

```text
authentication_mode = API_AND_CONFIG_MAP
```

AWS Backup for EKS requires the cluster to be accessible for backup/restore operations using supported authentication models documented by AWS. Clusters using **`API`** or **`API_AND_CONFIG_MAP`** are the modern paths (legacy `CONFIG_MAP`-only clusters are not the lab default).

**Lab checklist before enrolling:**

| Prerequisite | Project 1 status |
|--------------|------------------|
| Cluster ACTIVE | **Expected** (lab cluster exists) |
| Backup service-linked role / IAM permissions in account | **TBD** — verify in account |
| Backup vault | EFS automatic vault exists; **dedicated EKS vault TBD** |
| Backup plan selecting EKS resource type | **Not present** at inventory |
| Network path for AWS Backup to cluster API | Private/public endpoint design matches [`terraform/aws`](../terraform/aws) |

Operators must maintain **access entries** / IAM mapping so restore jobs can apply objects — document who owns that mapping outside Git.

---

## 4. Restore capabilities (conceptual)

AWS Backup restore workflows for EKS generally support:

| Restore style | Intent | Destructive? |
|---------------|--------|--------------|
| **Restore to existing cluster** | Merge/recreate supported objects from backup | Can overwrite namespaced resources with same name — **test in non-prod** |
| **Restore to new cluster** | DR pattern: fresh EKS + restore API objects | Safer for isolation; still need nodes, add-ons, GitOps |
| **Non-destructive partial restore** | Select namespaces or resource subsets where product allows | Preferred for lab experiments |

**Limitations (always verify in AWS docs):**

- Not all Kubernetes kinds or fields round-trip identically.
- Resources referencing AWS-generated names (LB ARNs, PVC volume handles) may need **reconciliation** after restore.
- **Secrets** restored from backup remain secrets — still rotate if compromise suspected.
- Restore does **not** recreate deleted **EC2 workers** or **EBS volumes** unless those are separate protected resources.

**Lab status:** No restore drill executed — all restore rows **TBD**.

---

## 5. Inventory findings (Section 25 — assessment time)

Evidence collected via [`scripts/_dr_inventory.sh`](../scripts/_dr_inventory.sh) pattern (run inside `platform-aws-tools`):

| Check | Result |
|-------|--------|
| EKS cluster describe | Name `platform-lab-aws-lab-eks`, auth mode **API_AND_CONFIG_MAP**, VPC **vpc-00c54a2d05f84fed6** |
| `aws backup list-backup-vaults` | Includes **automatic vault for EFS** (`aws/efs` style automatic plan) — **unrelated** to EKS lab |
| `aws backup list-backup-plans` | **No plan targeting this EKS cluster** at inventory |
| `aws backup list-protected-resources` | **No EKS protected resources** listed |
| EBS snapshots for `vol-05faa26874d720ecd` | **None** (owner self) at inventory |
| Kubernetes VolumeSnapshot CRDs | **Not installed** (`no snapshot CRDs`) |

**Assessment conclusion:** AWS Backup is **available in the account** but **not configured for Project 1 EKS**. DR for Kubernetes objects today relies on **Git + Argo CD**, not AWS Backup.

---

## 6. Comparison: AWS Backup EKS vs Git vs EBS snapshots

| Mechanism | RPO (lab, if used) | Best for | Project 1 status |
|-----------|-------------------|----------|------------------|
| **Git + Argo CD** | Last merge to `main` | Declarative app/platform K8s manifests | **Active** |
| **EBS snapshot (EC2 API or CSI)** | Snapshot schedule | Block data on `storage-demo` | **Not configured** |
| **AWS Backup for EKS** | Plan schedule | Supported K8s API objects | **Not enrolled** |
| **AWS Backup EFS automatic** | N/A for this lab | EFS file systems | **Exists; no EFS in EKS lab path** |

---

## 7. Recommended lab progression (no invented results)

| Step | Action | Success criteria | Status |
|------|--------|------------------|--------|
| 1 | Document assessment | This file | **Done** |
| 2 | Create backup vault + IAM (least privilege) | Vault visible, no secrets in Git | **TBD** |
| 3 | Enroll `platform-lab-aws-lab-eks` in plan | Protected resource appears in list | **TBD** |
| 4 | Run on-demand backup | Recovery point created | **TBD** |
| 5 | Non-destructive restore test (duplicate namespace or test cluster) | Known ConfigMap from `kubernetes/dr-lab/` restored | **TBD** |
| 6 | Pair with EBS snapshot for `storage-demo` | `state.txt` survives volume-level restore | **TBD** |

---

## 8. DR lab manifests (optional GitOps target)

Repo includes [`kubernetes/dr-lab/`](../kubernetes/dr-lab/) (namespace + ConfigMap marker `SNAPSHOT-CONFIG-A`). Intended for future backup/restore verification — **not claimed as synced or restored yet**.

---

## 9. Safety

- Do not paste backup vault credentials or IAM access keys into documentation.
- Test restores in isolated namespaces or clone clusters before touching `platform-lab` production namespace on AWS.
- Coordinate with [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) when whole cluster is new.

---

## 10. Related

- [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md)
- [`aws-storage-statefulset.md`](./aws-storage-statefulset.md)
- [`terraform-dr.md`](./terraform-dr.md)
