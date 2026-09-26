# Disaster Recovery Fundamentals (Project 1 — Section 25)

**Purpose:** Define how high availability (HA), backup, restore, disaster recovery (DR), and full rebuild differ in this lab, and map each control to what Project 1 actually protects today.  
**Scope:** VMware lab (`ckad-lab`) and AWS EKS lab (`platform-lab-aws` / `platform-lab-aws-lab-eks`).  
**Policy:** Do not treat resilience experiments as full DR proof until measured end-to-end. Mark **OBSERVED** only where this repo documents evidence; otherwise **TBD**.

---

## 1. Terminology (plain definitions)

| Term | Meaning | Typical failure it addresses |
|------|---------|------------------------------|
| **High availability (HA)** | The system keeps serving (or degrades gracefully) when a component fails, without restoring from backup. | Single pod/node/AZ component loss |
| **Backup** | A point-in-time copy of data or configuration stored outside the primary runtime. | Accidental delete, corruption, ransomware |
| **Restore** | Reconstruct runtime state from a backup (or snapshot) into an existing or new environment. | Data loss, volume rollback |
| **Disaster recovery (DR)** | Planned process to recover **business capability** after a large event (region/account/cluster loss), within agreed **RTO/RPO**. | Account compromise, regional outage, total cluster loss |
| **Rebuild** | Recreate infrastructure and platform from **declarative sources** (Git, Terraform, images) when backups alone are insufficient or absent. | Greenfield recovery, state loss, “everything is gone” |

These layers stack: HA reduces how often you need restore; backup/restore bounds data loss; DR/rebuild bounds downtime when the control plane or account is gone.

---

## 2. RPO and RTO (lab framing)

| Metric | Definition | Example (illustrative — not a lab SLA) |
|--------|------------|----------------------------------------|
| **RPO** (Recovery Point Objective) | Maximum acceptable **data** loss measured in time. | “We can lose up to 15 minutes of writes.” |
| **RTO** (Recovery Time Objective) | Maximum acceptable **downtime** before service is acceptable again. | “App must be reachable within 4 hours after regional failure.” |

**Project 1 lab targets (design intent, not contractual):**

| Capability | Target RPO (intent) | Target RTO (intent) | OBSERVED in Project 1 |
|------------|---------------------|---------------------|------------------------|
| Stateless app (`platform-lab`) on EKS | N/A (Git + image are source of truth) | Redeploy via GitOps after cluster exists | **TBD** (full cluster loss not exercised) |
| Stateful lab volume (`storage-demo` / EBS) | Depends on snapshot/backup cadence | Same-AZ node failure → pod Ready; snapshot restore | **≈ 6.3 min** T0→Ready ([`aws-storage-resilience.md`](./aws-storage-resilience.md)); snapshot restore ≈ **15 s** after PVC create ([`dr-lab-evidence.md`](./dr-lab-evidence.md)) |
| VMware `platform-lab` (2 replicas) | N/A for app data | Single worker kubelet outage → degraded then restored | Documented in [`vmware-node-failure-resilience.md`](./vmware-node-failure-resilience.md) (capacity path, not full DR) |
| Entire AWS account / VPC / EKS | Git + Terraform code; **no** remote state backup yet | Full rebuild sequence | **TBD** |
| Terraform state (local) | Last successful `apply` only | Re-import or re-apply from code | **TBD** (recovery drill not run) |

---

## 3. HA vs backup vs restore vs DR vs rebuild

```text
                    ┌─────────────────────────────────────────┐
                    │           Rebuild (greenfield)          │
                    │  Git + Terraform + registry + secrets   │
                    └───────────────────┬─────────────────────┘
                                        │ when platform is gone
                    ┌───────────────────▼─────────────────────┐
                    │     DR (runbooks, cross-region, etc.)   │
                    └───────────────────┬─────────────────────┘
                                        │
          ┌─────────────────────────────▼─────────────────────────────┐
          │              Restore (from backup/snapshot)               │
          └─────────────────────────────┬─────────────────────────────┘
                                        │
          ┌─────────────────────────────▼─────────────────────────────┐
          │        Backup (snapshots, AWS Backup, etcd backup…)         │
          └─────────────────────────────┬─────────────────────────────┘
                                        │
          ┌─────────────────────────────▼─────────────────────────────┐
          │   HA (replicas, PDB, multi-node, EKS managed control plane) │
          └─────────────────────────────────────────────────────────────┘
```

**Example (illustrative):** A bank might use HA for a payment API (3 AZs), nightly DB backups (RPO 24h), and a warm DR region (RTO 4h). **This lab** is not that tier; it uses the same vocabulary to practice engineering judgment.

---

## 4. What each Project 1 mechanism protects — and does not

### 4.1 Git (repository)

| Protects | Does not protect |
|----------|------------------|
| Desired Kubernetes manifests (`kubernetes/base`, overlays), GitOps project/app YAML mirrors, Terraform **code**, automation scripts, documentation | Running cluster state not committed (Secrets with real credentials, live `terraform.tfstate`, in-cluster objects someone applied outside Git) |
| Image **tag/digest promotion** history via commits (Jenkins → Git) | Docker Hub availability; unpushed local commits; deleted branches without backup |

### 4.2 Argo CD

| Protects | Does not protect |
|----------|------------------|
| Continuous reconcile of Git → cluster; self-heal/prune **for objects Argo owns** | Cluster existence; EKS control plane; node hardware; EBS volume contents unless app writes to Git |
| Fast re-application after cluster API returns | Terraform-provisioned AWS resources; data on PVCs; ALBs if Ingress finalizers block destroy paths |

**Lab instances:** VMware Argo CD **v3.5.3**; AWS Argo CD **v3.1.0** (see [`toolchain-inventory.md`](./toolchain-inventory.md)).

### 4.3 Terraform (`terraform/aws`)

| Protects | Does not protect |
|----------|------------------|
| Repeatable VPC, IAM, EKS, add-ons, Helm (LB controller, metrics-server, Argo CD), GitOps bootstrap **when code + state + credentials align** | Application Deployments owned by Argo (by design — see [`terraform/aws/README.md`](../terraform/aws/README.md)) |
| Documented destroy ordering (`pre-destroy-cleanup.sh`) for **controlled teardown** | Automatic DR; **`terraform destroy` is not normal DR** |

**Current gap:** **local state only** ([`terraform/aws/versions.tf`](../terraform/aws/versions.tf)). Losing the workstation copy of `terraform.tfstate` does not delete AWS resources, but it breaks safe incremental Terraform until state is recovered or reconstructed.

### 4.4 EBS volumes (lab StatefulSet)

| Protects | Does not protect |
|----------|------------------|
| Data for `storage-demo-0` on volume `vol-05faa26874d720ecd` while volume exists | Cross-AZ mobility (EBS is AZ-local — proven in [`aws-storage-resilience.md`](./aws-storage-resilience.md)) |
| Persistence across pod delete and **same-AZ** worker replacement | Account-level delete of volume; unprotected AZ outage |

**Lab binding:** PVC `data-storage-demo-0`, PV `pvc-612d84fb-dbd4-46d9-a17f-735216f0594d`, StorageClass `ebs-gp3`, AZ `ap-south-1b`.

### 4.5 CSI volume snapshots (Kubernetes + EBS)

| Protects | Does not protect |
|----------|------------------|
| *(When configured)* Point-in-time block copies for restore/new PVCs | Anything until snapshot schedule + restore drill exist |

**Inventory status (Section 25):** At DR inventory time, snapshot CRDs were **absent**. They were then installed via EKS managed add-on **`snapshot-controller` v8.6.0-eksbuild.8**; restore drill **lab-tested** ([`dr-lab-evidence.md`](./dr-lab-evidence.md)).

### 4.6 AWS Backup (EKS)

| Protects | Does not protect |
|----------|------------------|
| *(When EKS protection plans exist)* AWS-managed backup/restore patterns for supported EKS resources per AWS product model | Ad-hoc lab resources until enrolled; EBS data unless included in plan scope |

**Inventory status:** Account has **AWS Backup automatic vault/plan for EFS (`aws/efs`)** — unrelated to this EKS lab. **`list-protected-resources` showed no EKS protected resources** at inventory time. See [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md).

### 4.7 EKS “HA” (managed control plane)

| Protects | Does not protect |
|----------|------------------|
| AWS-operated control plane across AZs (standard EKS model) | Your worker nodes, your PVCs, your misconfiguration, your single NAT gateway (`enable_single_nat_gateway=true`) |
| API endpoint with `authentication_mode = API_AND_CONFIG_MAP` (this cluster) | IAM identity store outside AWS; lost kubeconfig without access entry/bootstrap |

**Lab cluster:** `platform-lab-aws-lab-eks`, Kubernetes **1.36.4**, region **`ap-south-1`**, VPC **`vpc-00c54a2d05f84fed6`**.

### 4.8 VMware lab HA patterns

| Protects | Does not protect |
|----------|------------------|
| 2+ app replicas, PDB, rolling updates, ingress + MetalLB | Single control-plane node (`k8s-ctrl-01`); host-only network; no etcd backup in repo |
| local-path storage for VMware StatefulSet lab | Host disk loss; VM snapshot policy (outside repo) |

**Nodes:** `k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02`; context **`ckad-lab`**, Kubernetes **1.31.14**.

---

## 5. Environment reference (Section 25)

| Field | VMware | AWS EKS |
|-------|--------|---------|
| Kube context | `ckad-lab` | `platform-lab-aws` (via **`platform-aws-tools`** container) |
| Kubernetes version | 1.31.14 | 1.36.4 |
| Nodes | k8s-ctrl-01, k8s-worker-01, k8s-worker-02 | Managed node group + prior temp group for storage lab |
| App image | `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` | Same (AWS overlay) |
| Primary GitOps apps | `platform-lab-local`, observability, storage/security labs | `platform-lab-aws`, `platform-storage-aws`, etc. |
| IaC state | N/A (manual/kubeadm lab) | Terraform **local state** under `terraform/aws` |

---

## 6. Section 25 lab targets vs observed status

| Exercise | Target outcome | Status |
|----------|----------------|--------|
| Document DR vocabulary and ownership boundaries | This document | **Done** |
| Terraform state / remote backend strategy | [`terraform-dr.md`](./terraform-dr.md) | **Done (design); remote backend not applied** |
| AWS account → platform rebuild runbook | [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) | **Conceptual; timings TBD** |
| AWS Backup for EKS assessment | [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) | **Assessed; no EKS plan yet** |
| Business continuity checklist | [`business-continuity.md`](./business-continuity.md) | **Done** |
| EBS snapshot + restore drill | Restored PVC with known `state.txt` | **Lab-tested** — POINT-A only; new volume ([`dr-lab-evidence.md`](./dr-lab-evidence.md)) |
| CSI VolumeSnapshot install + `VolumeSnapshotClass` | CRDs + one successful snapshot | **Lab-tested** (`v8.6.0-eksbuild.8`, `ebs-csi-snapclass`) |
| Full EKS loss rebuild (new cluster, same Git) | App + storage lab reachable | **TBD** |
| VMware control-plane failure / etcd restore | Documented procedure | **TBD** |
| DR lab manifests (`kubernetes/dr-lab/`) | Optional sync via GitOps | **Lab-tested** (App/namespace/selfHeal/Git drills; disposable resources cleaned) |

---

## 7. Safety and secrets

- Never commit `terraform.tfstate`, `terraform.tfvars`, kubeconfigs, or cloud credentials.
- DR exercises that terminate nodes, delete volumes, or destroy stacks require explicit approval and a written rollback path.
- Jenkins promotes image tags to Git; it does **not** deploy — recovery still flows **Git → Argo CD**.

---

## 8. Related documents

| Document | Role |
|----------|------|
| [`aws-storage-resilience.md`](./aws-storage-resilience.md) | **OBSERVED** same-AZ node failure (~6.3 min to Ready) |
| [`aws-storage-statefulset.md`](./aws-storage-statefulset.md) | EBS CSI + StatefulSet baseline |
| [`terraform-dr.md`](./terraform-dr.md) | State vs code, backend risks |
| [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) | Rebuild ordering |
| [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) | AWS Backup product fit |
| [`business-continuity.md`](./business-continuity.md) | People, DNS, registry, runbooks |
| [`runbooks/aws-api-failure.md`](./runbooks/aws-api-failure.md) | API degradation (not full DR) |
