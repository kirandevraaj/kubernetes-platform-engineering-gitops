# Disaster Recovery Interview Notes (Project 1)

Concise answers grounded in the **Kubernetes Platform Engineering & GitOps Lab**: VMware `ckad-lab` (Kubernetes **1.31.14**), AWS EKS `platform-lab-aws-lab-eks` (Kubernetes **1.36.4**, **`ap-south-1`**, auth **`API_AND_CONFIG_MAP`**, VPC **`vpc-00c54a2d05f84fed6`**), EBS lab volume **`vol-05faa26874d720ecd`**, Terraform **local state**, app image **`kirandevraaj/platform-lab:0.1.4`** @ **`sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`**.

Master reference: [`disaster-recovery-master-guide.md`](./disaster-recovery-master-guide.md). Fundamentals: [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md). Scenarios: [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md).

**Test honesty:** **Lab-tested** = documented evidence in this repo; **Documented only** = procedure without full drill on production-like paths.

---

## 1. Difference between HA and DR?

**HA** keeps service available (or acceptably degraded) when a **component** fails—no restore from backup. Examples: second `platform-lab` replica, dual ingress controllers, EKS managed control plane, EBS reattach after same-AZ node loss (~**6.3 min** — **lab-tested**).

**DR** is the **planned process** to restore **platform capability** after a **large** event (cluster/account/region loss, unrecoverable data) within **RPO/RTO**, often involving rebuild + backup restore + verification. Full EKS loss rebuild in Project 1 is **documented only** (**TBD** timing).

---

## 2. What is RPO?

**Recovery Point Objective** — maximum acceptable **data loss**, usually as time since the last durable copy.

In this lab: committed Git config ≈ **RPO 0** for desired state; `storage-demo` EBS data has **undefined RPO** (no snapshots on `vol-05faa26874d720ecd` at inventory); Terraform state RPO = last backup copy of local `terraform.tfstate` (**TBD** discipline).

---

## 3. What is RTO?

**Recovery Time Objective** — maximum acceptable **downtime** until service is acceptable again.

Observed examples: pod delete on `storage-demo-0` ~**14 s**; same-AZ worker failure → pod Ready ~**6.3 min** (**lab-tested**). Argo Application re-apply target &lt; 10 min (**TBD**). Full cluster rebuild **TBD**.

---

## 4. Why is Git not a backup for application data?

Git stores **declarative configuration** (YAML, Terraform **code**, docs)—not block storage contents. The lab’s `state.txt` on EBS **`vol-05faa26874d720ecd`** never lives in Git. Restoring Git redeploys the StatefulSet but **does not recreate** deleted or corrupted volume data without **EBS snapshot / restore** or same intact volume.

---

## 5. What does Argo CD recover?

Argo reconciles **Git desired state → cluster** for resources it manages: Deployments, Services, Ingress, HPA, PDB, NetworkPolicy, ConfigMaps, Application CRs from repo paths, etc. After Application re-apply or bad-commit **revert**, it restores **configuration** to match Git. Self-heal fixes live drift (**lab-tested** on VMware annotation experiment).

---

## 6. What does Argo CD not recover?

- **AWS infrastructure** (VPC, EKS, node groups) — Terraform.
- **EBS volume data** — CSI/snapshots.
- **Deleted EBS volumes** or snapshots never taken.
- **Container images** — registry pull.
- **Terraform state** — not in Git.
- **Cluster existence** — if EKS is gone, reinstall Argo via Terraform first.
- **Secrets/credentials** not stored in Git.
- Workloads **orphaned** after Application delete may remain until manually pruned—Argo metadata alone is not a full CMDB backup.

---

## 7. What does EBS protect?

While the volume exists and is bound to the pod in the **same AZ**, EBS protects **block data** across pod delete and **same-AZ** worker replacement. Lab PVC `data-storage-demo-0` → PV → **`vol-05faa26874d720ecd`** in **`ap-south-1b`** (**lab-tested** persistence path).

---

## 8. What does EBS NOT protect?

- **Cross-AZ** attach (pod in **1a**, volume in **1b** → Pending — **lab-tested** constraint).
- **Volume delete** or account-level loss without snapshots.
- **AZ-wide** outage for single-AZ volume.
- **Logical corruption/overwrites** — snapshots or app-level backup needed; overwrite on production volume **not tested** in lab.
- **Kubernetes objects** — those are Git/Argo/AWS Backup (if enrolled).

---

## 9. How does an EBS snapshot differ from an EBS volume?

A **volume** is the live attachable block device used by the node/Pod. A **snapshot** is a **point-in-time, regional** copy used to **create new volumes** (optionally in another AZ in the same region). Snapshots are the basis for **restore RPO**; the lab had **no snapshots** on the main volume at Section 25 inventory.

---

## 10. How would you recover a lost EBS-backed PVC?

1. **If volume still exists:** ensure PVC/PV binding and pod scheduled in **same AZ** as volume (same-volume path — **lab-tested** for pod/node cases).
2. **If volume gone but snapshot exists:** create snapshot → new volume → new PVC with `dataSource` (CSI VolumeSnapshot) or EC2 API workflow → mount in **`dr-storage-restore`** for drills ([`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md)).
3. **If no snapshot:** data **unrecoverable**; recreate empty StatefulSet from Git only.

Requires **snapshot-controller** add-on (**v8.6.0-eksbuild.8** planned) + VolumeSnapshotClass — **TBD** in lab.

---

## 11. How does CSI snapshot work?

1. Admin installs **EBS CSI driver** (present) + **snapshot controller** (being added) + **VolumeSnapshotClass**.
2. User creates **VolumeSnapshot** referencing PVC.
3. **External snapshotter** creates EBS snapshot; **VolumeSnapshotContent** holds handle.
4. New PVC references snapshot as **dataSource**; CSI provisions new volume and binds.

At inventory: **no snapshot CRDs** — workflow **documented only**.

---

## 12. What is AWS Backup for EKS?

AWS Backup can enroll an **EKS cluster** in a **backup plan**, storing **supported Kubernetes API objects** as recovery points in a vault—with retention/lifecycle. It is **API-object recovery** orchestrated by AWS, **not** a full clone of every byte on disk unless paired with EBS/volume policies. See [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md).

---

## 13. What does AWS Backup NOT include?

Without separate protection: **EBS data bytes**, **Terraform-managed AWS infra**, **Docker images**, **Terraform state**, **unsupported CRDs**, **etcd** (managed by AWS for CP), **metrics history**, **manual console drift**, and **everything outside plan scope**. Project 1 had **no EKS protected resources** at inventory—only unrelated **EFS automatic** vault.

---

## 14. How would you rebuild an EKS cluster?

Forward rebuild from Git + Terraform ([`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md)): IAM → VPC/NAT → EKS **1.36.4** → node group → add-ons (EBS CSI, **snapshot-controller**) → AWS LB Controller → metrics-server → Argo Helm → GitOps bootstrap → sync Applications (`platform-lab-aws`, storage, security, observability). Register repo creds; verify ALB and digest-pinned pods. **Documented only** — not executed as full drill.

---

## 15. Where does Terraform fit in DR?

Terraform **rebuilds the cloud platform shell**: VPC **`vpc-00c54a2d05f84fed6`**, EKS, IAM, add-ons, Argo install, bootstrap Application. It does **not** replace Argo for app manifests or EBS data. **`terraform destroy` is not DR.**

---

## 16. What happens to Terraform state?

State maps resource addresses → AWS IDs. **Local state** (lab today) lives on the workstation/`platform-aws-tools` workspace—**gitignored**. Lose state without backup → AWS may still run, but Terraform risks **duplicate creates** or failed destroys until **import** or **greenfield** stack. Remote S3 backend is **designed, not applied** ([`terraform-dr.md`](./terraform-dr.md)).

---

## 17. What happens if GitHub is unavailable?

Argo **cannot fetch** new commits; Jenkins cannot poll/push promotions; humans cannot merge fixes. **Running clusters keep running** with last synced config. Mitigations: local/mirror clone, cached repo-server data, secondary remote (**TBD** in lab). Unpushed commits are at risk.

---

## 18. What happens if Docker Hub is unavailable?

New pods needing **pull** fail (`ImagePullBackOff`); nodes with cached layers may keep running. Lab pins **digest** in Git—recovery needs registry access or **ECR mirror** (**TBD**). Image: `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b59…872ff`.

---

## 19. How do you recover Argo?

1. Fix transient: restart pods / Helm upgrade in `argocd` namespace.
2. Reinstall: Terraform Helm release on new cluster.
3. Re-apply **Applications**, **AppProjects**, **ApplicationSets** from Git (`gitops/applications/`).
4. Re-register **repo credentials** from secure store (not Git).
5. Sync and verify Health/Synced.

Application delete drill on **`platform-dr-recovery`**: **documented only** (**TBD**).

---

## 20. How do you recover Jenkins?

Jenkins is **outside** the cluster (Docker Desktop Compose). Restore container; restore **credential store** (`dockerhub-platform-lab`, `github-platform-lab` — names only); replay builds from **`Jenkinsfile` in Git**. CI outage does **not** stop running EKS/VMware workloads (**documented only** for outage drill).

---

## 21. What if the entire AWS AZ fails?

Nodes in that AZ disappear. Stateless pods reschedule if capacity exists elsewhere. **EBS in failed AZ** is unavailable until AZ recovery—lab volume **`ap-south-1b`** would block `storage-demo` unless you **restore snapshot to volume in surviving AZ** (requires prior snapshot). **Not fully tested**—only AZ scheduling constraint **lab-tested**.

---

## 22. What if the entire AWS Region fails?

Total loss of **`ap-south-1`** stack: EKS, VPC, volumes, ALB. Recovery = rebuild in **new region** from Terraform + Git + (if configured) **cross-region snapshot copies** + DNS update. **Documented only**; no second region in lab.

---

## 23. Why isn't EBS itself multi-AZ storage?

EBS volumes are **AZ-scoped** block devices—replication and durability are within that AZ’s storage infrastructure, not portable live attachment across AZs. Multi-AZ **applications** use multiple volumes/replicas or different storage (EFS, RDS Multi-AZ). Lab proved pod in **1a** cannot mount volume in **1b**.

---

## 24. How would you design multi-AZ stateful applications?

Patterns: **one replica per AZ** with **PVC per AZ** (data sharded); **EFS/RDS** with multi-AZ; **operators** with cross-AZ replication; **frequent snapshots** + restore runbooks; avoid single PVC on single AZ for critical data. Project 1 intentionally uses **single replica + single EBS** for learning.

---

## 25. How would you validate a backup?

Restore to **isolated** scope (`dr-storage-restore`, test cluster, or duplicate namespace), then **verify** known content (e.g., `state.txt` marker, ConfigMap `SNAPSHOT-CONFIG-A` in [`kubernetes/dr-lab/`](../kubernetes/dr-lab/)), compare checksums/timestamps, and record **RPO/RTO** milestones. **Not yet executed** for snapshots in this lab.

---

## 26. Why is "backup succeeded" insufficient?

Success only proves **creation** of a recovery point—not **restorability**, **correct scope**, **dependency availability** (IAM, CSI, cluster), **operator skill**, or **verification**. DR requires reconstruct + verify within RTO/RPO ([`disaster-recovery-master-guide.md`](./disaster-recovery-master-guide.md) master principle).

---

## 27. How do you prove restore works?

Run a **scheduled restore drill** in non-prod: restore → mount → read known data → run app smoke test → document volume IDs and timestamps. Delete disposable resources after evidence. Project 1 status: **TBD** for EBS; Git revert + Argo **partially proven** via self-heal experiments.

---

## 28. How do you measure RTO?

Define **T0** (detection) → **T3** (verification pass). Example milestones: incident logged, recovery action started, Argo Synced, HTTP 200 via ALB/VIP, `state.txt` correct. Compare elapsed time to target. Same-AZ node recovery **~6.3 min** is an observed **partial RTO** for one workload—not whole platform.

---

## 29. How do you measure RPO?

Identify last recovery point time **T_snap** (snapshot timestamp or Git commit for config). At failure **T_loss**, quantify data changed after **T_snap** (files, DB rows, config drift). For config-only incidents, RPO = commits after last good SHA. Without snapshots, EBS **catastrophic** RPO = **total loss**.

---

## 30. How do you test DR without destroying production?

Use **disposable scopes** only: namespaces **`dr-lab`**, **`dr-storage-restore`**, Application **`platform-dr-recovery`**, temporary snapshots/volumes. **Never** delete `platform-lab`, `storage-lab`, `security-lab`, observability, main EKS/VPC, or **`vol-05faa26874d720ecd`**. Tabletop + read-only `plan` for Terraform. See [`dr-baseline-inventory.md`](./dr-baseline-inventory.md#4-safety-boundaries-for-section-25).

---

## 31. What is a DR runbook?

A **step-by-step operational document** with triggers, severity, read-only checks, protect-data steps, recovery order, verification, and rollback. Project 1 runbooks: [`runbooks/aws-eks-disaster-recovery.md`](./runbooks/aws-eks-disaster-recovery.md), [`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md), [`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md), [`runbooks/terraform-infrastructure-recovery.md`](./runbooks/terraform-infrastructure-recovery.md).

---

## 32. How do you prevent credentials becoming the DR bottleneck?

Store secrets **outside Git** (Jenkins cred store, AWS SSO, encrypted state backups); document **credential names** and rotation paths in [`business-continuity.md`](./business-continuity.md); use **access entries** for EKS; break-glass accounts sparingly; practice recovery without pasting secrets into tickets. Restore **identity plane** early in rebuild sequence.

---

## 33. What dependencies exist outside Kubernetes?

AWS account/IAM, Terraform state location, **GitHub**, **Docker Hub**, workstation/VMware hypervisor, Jenkins host, DNS/hosts file (`platform-lab.local`), MetalLB pool, internet/NAT for pulls, AWS APIs, operator’s SSO login. Failure of any can block recovery even if cluster YAML is perfect.

---

## 34. How do you automate DR?

Candidates: scripted **`platform-automate dr verify`** (planned), inventory checks (`scripts/_dr_inventory.sh`), Terraform plan in CI, Argo health checks, snapshot age alarms, AWS Backup on-demand jobs. Automation must respect **confirm gates** and **allow-lists**—same discipline as Section 24 automation. Full auto-rebuild **not** implemented.

---

## 35. What would you back up for an EKS platform?

| Asset | Mechanism |
|-------|-----------|
| App/platform K8s manifests | Git (primary) + optional AWS Backup EKS |
| Terraform code | Git |
| Terraform state | S3/versioned backup (target) |
| EBS PVC data | EBS snapshots / CSI VolumeSnapshot |
| Container images | ECR mirror / retain digests in Git |
| Argo repo creds | Secret manager |
| Observability config | Git; TSDB optional |
| Runbooks/docs | Git |

Lab gaps: **EBS snapshots**, **remote state**, **EKS AWS Backup enrollment**.

---

## 36. What would you rebuild rather than restore?

**Stateless app tiers** from Git + image digest. **VPC/EKS/node groups/add-ons** from Terraform code (forward apply). **Observability stack** from GitOps. **Immutable nodes** (MNG replace). Prefer rebuild when **restore is riskier** than declarative recreate (unknown drift, corrupt backup). **Stateful data** must **restore** from snapshot if volume gone—rebuild alone loses bytes.

---

## 37. What is immutable infrastructure in DR?

Replace failed **nodes** and **pods** from declared config rather than SSH-repair snowflakes. New instances, new volumes from snapshots, new deployments from Git—**cattle, not pets**. Lab MNG and GitOps align with this; VMware single control-plane is **not** immutable HA.

---

## 38. What is configuration drift during DR?

Manual `kubectl edit`, console changes, or partial restores can leave **actual ≠ Git**. Under stress, teams patch live—Argo self-heal may fight or hide intent. Recovery discipline: **fix Git first**, sync, avoid uncommitted cluster hotfixes as source of truth. Export UI-only Argo changes back to Git ([`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md)).

---

## 39. How does GitOps help disaster recovery?

Git is **durable desired state** with audit history (`revert`), multi-environment overlays (VMware/AWS), and automated reconcile after cluster returns. Argo re-applies **known-good SHA** quickly—**config RPO ≈ 0** for committed state. Pair with Terraform for infra and snapshots for data.

---

## 40. How does observability help validate recovery?

After restore, use Prometheus **`up`**, kube-state-metrics **Ready** counts, Grafana dashboards, and synthetic HTTP checks (ALB or MetalLB VIP) to prove **service**, not just **sync**. Observability does not restore data—it **reduces false “done”** declarations. Metrics history may be lost; config redeploys from Git (`platform-lab-observability`, AWS observability app).

---

## Quick scenario crib sheet

| Question | One-line answer |
|----------|-----------------|
| Pod vs cluster loss? | Pod: controller (**tested**). Cluster: Terraform + Argo (**TBD**). |
| CI vs runtime outage? | Jenkins down ≠ cluster down. |
| Best lab RTO evidence? | **~6.3 min** EBS same-AZ node path. |
| Biggest data gap? | No EBS snapshot on main volume at inventory. |
| Biggest IaC gap? | **Local Terraform state**. |

---

## Related

- [`disaster-recovery-master-guide.md`](./disaster-recovery-master-guide.md) — Parts I–X
- [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md) — 18 scenarios
- [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) · [`terraform-dr.md`](./terraform-dr.md)
