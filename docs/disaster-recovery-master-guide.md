# Disaster Recovery Master Guide

**Status:** Section 25 MASTER REFERENCE for Project 1 — Kubernetes Platform Engineering & GitOps Lab.

**Environments:** VMware `ckad-lab` (Kubernetes **1.31.14**) · AWS EKS `platform-lab-aws-lab-eks` (Kubernetes **1.36.4**, region **`ap-south-1`**, auth **`API_AND_CONFIG_MAP`**, VPC **`vpc-00c54a2d05f84fed6`**).

**App artifact (pinned):** `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`.

**Honesty policy:** **Lab-tested** means this repo documents measured or executed evidence. **Documented only** means procedure exists but destructive or full-path drill not run on production-like resources. **TBD** means planned Section 25 work not yet recorded.

**Companion Q&A:** [`disaster-recovery-interview-notes.md`](./disaster-recovery-interview-notes.md).

**Cross-links (Section 25 corpus):**

| Document | Role |
|----------|------|
| [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md) | Vocabulary, RPO/RTO table, mechanism boundaries |
| [`dr-baseline-inventory.md`](./dr-baseline-inventory.md) | Read-only inventory snapshot (2026-09-26) |
| [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md) | 18 scenarios, test status, automation candidates |
| [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) | AWS Backup assessment (no EKS enrollment at inventory) |
| [`terraform-dr.md`](./terraform-dr.md) | Code vs state, local backend risks |
| [`business-continuity.md`](./business-continuity.md) | People, registry, DNS, credentials (names only) |
| [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) | Ordered AWS platform rebuild |
| [`runbooks/aws-eks-disaster-recovery.md`](./runbooks/aws-eks-disaster-recovery.md) | EKS incident flow |
| [`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md) | Same-volume vs snapshot restore |
| [`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md) | GitOps recovery |
| [`runbooks/terraform-infrastructure-recovery.md`](./runbooks/terraform-infrastructure-recovery.md) | State backup, plan, apply discipline |

---

## Part I — Concepts

### 1. HA vs Backup vs Restore vs DR

These terms are **not interchangeable**. Project 1 uses all five layers; most prior milestones proved **HA**, not full **DR**.

| Layer | Definition | Project 1 example | Evidence |
|-------|------------|-------------------|----------|
| **HA** | Service continues (or degrades gracefully) without restoring from backup | 2× `platform-lab` replicas, ingress HA, EKS managed control plane, PDB | **Lab-tested** (pod delete, ingress HA, same-AZ node + EBS) |
| **Backup** | Point-in-time copy stored outside primary runtime | EBS snapshot, AWS Backup recovery point, Git history, Terraform state copy | Git **active**; EBS/AWS Backup EKS **not configured** at inventory |
| **Restore** | Reconstruct from backup into existing or new environment | VolumeSnapshot → new PVC in `dr-storage-restore`; `git revert` | Same-volume **lab-tested**; snapshot path **documented only** |
| **DR** | End-to-end recovery of **capability** within agreed **RPO/RTO** after large failure | Rebuild EKS + GitOps + optional data restore | Mostly **documented only**; matrix in [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md) |
| **Rebuild** | Recreate platform from declarative sources when runtime is gone | `terraform/aws` + Git + Argo bootstrap + registry pull | **Documented only** (no full cluster loss drill) |

**Master principle (Section 25):** DR is not “Do we have a backup?” It is: **Can we reconstruct the service and verify it within RTO while losing no more data than RPO allows?** A backup counts only if it exists, is accessible, restorable, dependencies are recreatable, verification passes, and operators know the runbook.

See also the stack diagram in [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md#3-ha-vs-backup-vs-restore-vs-dr-vs-rebuild).

### 2. RPO

**Recovery Point Objective** — maximum acceptable **data** loss, usually expressed as time since last durable copy.

| Asset | Lab intent (not SLA) | OBSERVED / inventory |
|-------|----------------------|----------------------|
| Stateless `platform-lab` config | **0** for committed Git (`main`) | Argo tracks Git; unpushed commits at risk |
| Stateful `storage-demo` EBS data | Depends on snapshot cadence | **Undefined RPO** — no snapshots on `vol-05faa26874d720ecd` at inventory |
| Terraform infrastructure code | Last merge to Git | Git **0** for committed `.tf` |
| Terraform state | Last successful `apply` / backup copy | **Local state** — RPO = last manual copy (**TBD** drill) |
| Prometheus TSDB | Not in DR scope | Rebuild empty or accept loss |
| Jenkins promotion state | Last Git commit with digest | CI down does not roll back running pods |

Measure RPO at **detection** of data loss: compare live `state.txt` (or DB) to last recovery point timestamp.

### 3. RTO

**Recovery Time Objective** — maximum acceptable **downtime** before capability is acceptable again.

| Scenario | Lab target (design intent) | OBSERVED |
|----------|----------------------------|----------|
| Single pod delete (stateless) | Minutes → often seconds | VMware/AWS app: seconds scale (**lab-tested**) |
| Pod delete (`storage-demo-0`) | &lt; 10 min | **~14 s** to Ready ([`aws-storage-statefulset.md`](./aws-storage-statefulset.md)) |
| Same-AZ worker failure + EBS reattach | &lt; 15 min | **≈ 6.3 min** T0→Ready ([`aws-storage-resilience.md`](./aws-storage-resilience.md)) |
| Argo Application re-apply | &lt; 10 min | **TBD** (`platform-dr-recovery`) |
| EBS snapshot restore drill | Measure T0→data verified | **TBD** |
| Full EKS rebuild | Hours (documented model) | **TBD** |
| VMware control-plane loss | Hours / manual rebuild | **TBD** (single `k8s-ctrl-01`) |

RTO starts at **T0** (detection or declared incident), not when someone starts reading docs.

### 4. Failure Domains

A **failure domain** is the blast radius of a single fault.

| Domain | VMware lab | AWS lab |
|--------|------------|---------|
| Pod / container | kubelet, probes, image pull | Same + IRSA/pod identity at app edge |
| Node | `k8s-worker-01/02` | Managed node group instances in **1a/1b** |
| AZ | N/A (single-site VMs) | **`ap-south-1a` vs `1b`** — EBS bound to **1b** for lab volume |
| Control plane | Single `k8s-ctrl-01` (**SPOF**) | **AWS-managed** EKS CP |
| GitOps plane | Argo CD in `argocd` | Argo CD Helm from Terraform |
| CI plane | Jenkins on Docker Desktop | Same (not on cluster) |
| Registry | Docker Hub | Same |
| IaC plane | N/A | Terraform + **local state** |
| Region | N/A | **`ap-south-1` only** — no warm DR region |
| Account | Shared AWS account | IAM, SSO, billing |

Use [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md) to map symptoms → domain → runbook.

### 5. Recovery Domains

A **recovery domain** is *where you get truth from* when rebuilding.

| Domain | Source of truth | Recovers | Does not recover |
|--------|-----------------|----------|------------------|
| **Git** | GitHub `main` + history | K8s manifests, Argo Application YAML, Terraform **code**, docs | EBS bytes, Terraform **state**, live Secrets values not in Git |
| **Container registry** | Docker Hub digest | Immutable image layers for `0.1.4` | Running pod memory; unpushed local images |
| **Terraform** | `terraform/aws` + state | VPC, EKS, add-ons, Argo Helm, bootstrap | App Deployments (Argo), PVC data |
| **Argo CD** | Reconcile Git → cluster | In-cluster desired state convergence | AWS VPC; EBS contents |
| **EBS / snapshots** | `vol-05faa26874d720ecd` or snapshot | Block data for `storage-demo` | Kubernetes object graph |
| **AWS Backup (EKS)** | Vault recovery points (if enrolled) | Supported K8s API objects per AWS model | Not enrolled at inventory — see [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) |
| **Observability** | Git (`platform-lab-observability` apps) | Grafana/Prometheus **config** | Historical metrics |
| **Jenkins** | `Jenkinsfile` in Git | Pipeline definition | Credential store (out-of-band) |
| **IAM / access** | AWS account | API access, EKS access entries | Must exist before automation works |

### 6. Data vs Configuration

| Type | Examples in Project 1 | Recovery mechanism |
|------|----------------------|-------------------|
| **Configuration** | Deployment replicas, Ingress rules, HPA, NetworkPolicy, Argo Apps | Git + Argo |
| **Infrastructure config** | VPC CIDR, node group size, add-on versions | Terraform code + state |
| **Application data** | `storage-lab` `state.txt` on EBS | Same volume (HA path) or snapshot (restore path) |
| **Secrets** | Jenkins creds, `terraform.tfvars`, cluster-admin kubeconfig | Out-of-band vault; **never** commit values |
| **Ephemeral** | emptyDir, container writable layer | Redeploy pod |
| **Observability data** | Prometheus TSDB | Optional backup; lab accepts rebuild |

**Interview trap:** Git is configuration recovery, not application data backup ([`disaster-recovery-interview-notes.md`](./disaster-recovery-interview-notes.md) Q4).

---

## Part II — Kubernetes DR

### 7. Pod Recovery

Kubernetes recreates pods when controllers see a shortfall.

| Workload | Controller | Lab behavior |
|----------|------------|--------------|
| `platform-lab` Deployment | ReplicaSet | Delete pod → new pod; Service endpoints update |
| `storage-demo-0` | StatefulSet | Same ordinal, same PVC |

**Lab-tested:** VMware pod self-healing; AWS `storage-demo-0` ~**14 s** after pod delete. **Documented only:** sustained NotReady injection on AWS app.

Argo **self-heal** reverts live drift to Git — **lab-tested** on VMware annotation experiment (~0.22 s detect — [`vmware-argo-self-healing.md`](./vmware-argo-self-healing.md)).

### 8. ReplicaSet/StatefulSet Recovery

- **ReplicaSet:** tied to Deployment revision; lost RS recreated on Deployment apply.
- **StatefulSet:** stable network ID + PVC template; ordinal 0 keeps `data-storage-demo-0`.

**Lab-tested:** StatefulSet + same PVC/PV/EBS after pod and same-AZ node events. **Not tested:** StatefulSet object deleted with retain policy vs cascade (use Git + Argo, not manual guess).

Pin images by **digest** in overlays so recovery does not accidentally pull a mutated tag.

### 9. Namespace Recovery

Deleting a namespace removes namespaced objects. **PVCs and data** go with it unless finalizers/retention policies say otherwise — namespace recreate from Git **does not** resurrect deleted EBS volumes.

**Safe drill scope:** `dr-lab` only ([`dr-baseline-inventory.md`](./dr-baseline-inventory.md#4-safety-boundaries-for-section-25)).

**Recovery:** Argo Application with `CreateNamespace=true` + manifests in Git. **Status:** **Documented only** (**TBD** timing).

**Never** use this drill on `platform-lab`, `storage-lab`, `security-lab`, `observability`.

### 10. GitOps Recovery

GitOps recovery means **restoring desired state in Git** (or reverting bad commits), then letting Argo sync.

| Failure | Fix |
|---------|-----|
| Bad merge on `main` | `git revert` → push → Argo sync |
| Cluster empty but Git intact | Install Argo + Applications → sync |
| Live drift | Self-heal or sync (prefer Git fix for intentional change) |

**Lab-tested:** self-heal for drift. **Documented only:** bad ConfigMap on `dr-lab` + revert timing.

Jenkins **does not** deploy to cluster — recovery path remains **Git → Argo** ([`git-argo-recovery.md`](./runbooks/git-argo-recovery.md)).

### 11. Argo Recovery

Two Argo instances: VMware **v3.5.3**, AWS **v3.1.0** ([`toolchain-inventory.md`](./toolchain-inventory.md)).

| Component loss | Recovery |
|----------------|----------|
| Application CR deleted | Re-apply from `gitops/applications/` |
| AppProject / ApplicationSet | Re-apply from Git; advanced lab sets on VMware only |
| Argo CD server/repo-server down | Helm/Terraform reinstall; repo credentials out-of-band |
| Redis / application controller | Kubernetes reschedule (HA not fully modeled in lab) |

**Lab-tested:** Application sync health on production-like apps (normal ops). **Documented only:** delete `platform-dr-recovery` Application (**TBD**). **Not safe to test:** full `argocd` namespace outage on sole GitOps plane.

### 12. RBAC Recovery

Security lab manifests in Git define Roles, Bindings, ServiceAccounts, PSA labels, NetworkPolicies.

| Event | Recovery |
|-------|----------|
| Accidental RBAC delete | Argo sync from `platform-security-*` apps |
| Lockout (`can-i` deny) | Break-glass cluster-admin (document access path outside Git) |

**Lab-tested:** security lab deployed and validated in Section 22. **Documented only:** deliberate RBAC delete recovery timing.

### 13. Secrets Recovery

| Secret type | In Git? | Recovery |
|-------------|---------|----------|
| App config (non-sensitive) | ConfigMaps yes | Git |
| TLS / Docker pull / repo passwords | **No** (SealedSecrets/External Secrets **not** in baseline) | Recreate from vault; rotate if compromised |
| ServiceAccount tokens | Projected / bound | Recreated with SA |
| Argo repo creds | K8s Secret in cluster | Re-bootstrap from secure store |

AWS Backup may include Secret **objects** if enrolled — values still sensitive; rotation policy applies ([`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md)).

---

## Part III — AWS DR

### 14. EKS Control Plane Resilience

EKS control plane is **AWS-operated**, multi-AZ within the region. Lab cluster **`platform-lab-aws-lab-eks`**, platform version **eks.14**, K8s **1.36.4**.

**Protects:** Kubernetes API availability (within AWS SLA model). **Does not protect:** your node groups, your PVCs, your misconfiguration, your single NAT gateway (`enable_single_nat_gateway=true` in Terraform).

**Auth mode:** **`API_AND_CONFIG_MAP`** — access entries and aws-auth/config map both matter for human/automation access during recovery.

**Not safe to test:** simulated CP failure. **Documented only:** rely on AWS remediation + `aws eks describe-cluster`.

### 15. Node Groups

Managed node group **`platform-lab-aws-lab-managed`**: t3.medium, desired 2, min 1 / max 3.

| Event | Behavior |
|-------|----------|
| Instance failed | MNG replaces instance |
| AZ loss | Nodes in affected AZ gone; pods reschedule if capacity elsewhere |
| EBS pod on wrong AZ | Pending until same AZ worker exists |

**Lab-tested:** same-AZ replacement with EBS reattach (~**6.3 min**). **Documented only:** full AZ loss.

### 16. AZs

Subnets span **`ap-south-1a`** and **`ap-south-1b`**. Deployments can spread; **EBS cannot**.

**Lab-tested:** scheduling pod to **1a** while volume in **1b** fails (expected Pending) — [`aws-storage-resilience.md`](./aws-storage-resilience.md). This is **constraint proof**, not AZ disaster recovery.

### 17. EBS

Lab volume **`vol-05faa26874d720ecd`**: 1 GiB, **ap-south-1b**, bound to PVC `data-storage-demo-0`, StorageClass **`ebs-gp3`** (WaitForFirstConsumer).

| Protects | Does not protect |
|----------|------------------|
| Data across pod delete / same-AZ node replace | Cross-AZ attach, volume delete, account compromise |
| Persistence for StatefulSet lab | AZ-wide outage without snapshot |

**Do not delete** this volume in exercises. Disposable restore uses **`dr-storage-restore`** namespace only.

### 18. EBS Snapshots

EBS snapshots are **regional** point-in-time copies used to create **new** volumes (possibly in another AZ in the same region).

**Inventory:** **no snapshots** on lab volume at Section 25 inventory. **RPO undefined** until cadence exists.

**Documented only:** snapshot create/restore drill. Use markers `SNAPSHOT-POINT-A/B` in disposable paths ([`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md)).

### 19. CSI Snapshots

Requires:

1. **EBS CSI driver** — **ACTIVE** (`aws-ebs-csi-driver` v1.66.0-eksbuild.1 at inventory).
2. **Snapshot controller** — **not installed** at inventory; **being added** as EKS managed add-on **`snapshot-controller` v8.6.0-eksbuild.8** (Section 25 progression).
3. **VolumeSnapshotClass** + **VolumeSnapshot** CRDs — **absent** at inventory.

Workflow (when installed): `VolumeSnapshot` → `VolumeSnapshotContent` → EBS snapshot ID → restore via `dataSource` on new PVC.

**Status:** **Documented only** until CRDs + successful snapshot **TBD**.

### 20. AWS Backup

Account has **EFS automatic** vault/plan only — **not** EKS lab path. **`list-protected-resources` empty** for EKS at inventory.

See [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) for includes/excludes and enrollment checklist.

**Status:** Assessment **done**; execute backup/restore **TBD**.

### 21. Cross-AZ

**Stateless:** run replicas across AZs (Deployment + topology spread where configured). **Stateful on EBS:** single-AZ volume — use snapshot restore to new AZ or move to EFS/RDS multi-AZ pattern (out of current lab scope).

**Lab-tested:** AZ constraint. **Not tested:** full AZ failure simulation.

### 22. Cross-Region

No second region stack in Project 1. Recovery model: new region Terraform variables + Git overlays update + snapshot **copy** (if configured) + DNS cutover (**Route53 not in lab baseline**).

**Documented only** — [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md).

---

## Part IV — Infrastructure DR

### 23. Terraform

Root module [`terraform/aws`](../terraform/aws) owns VPC **`10.50.0.0/16`**, IAM, EKS, add-ons, AWS LB Controller, metrics-server, Argo CD Helm, GitOps bootstrap (AppProject + Application).

**DR role:** forward **rebuild** of cloud shell. **`terraform destroy` is not DR** — controlled teardown only.

Apply workspace: **`platform-aws-tools`** container (Terraform may be absent from Windows PATH).

### 24. Terraform State

**Current:** **local backend** ([`terraform/aws/versions.tf`](../terraform/aws/versions.tf)), files **gitignored**.

| State lost? | AWS resources |
|-------------|---------------|
| Yes | Still running — but Terraform may propose duplicates |
| No | Incremental plan/apply safe |

**Interim:** copy `terraform.tfstate` + `.backup` after each successful apply (encrypted, off-repo). **Remote S3 + DynamoDB lock:** design in [`terraform-dr.md`](./terraform-dr.md) — **not applied**.

**Drill:** **TBD**.

Known IDs for import discussions (non-secret): VPC `vpc-00c54a2d05f84fed6`, cluster `platform-lab-aws-lab-eks`, volume `vol-05faa26874d720ecd`.

### 25. VPC

VPC **`vpc-00c54a2d05f84fed6`**, private/public subnets in **1a/1b**, **single NAT** (cost-conscious, **HA weakness** for private egress).

Loss of VPC = full Terraform rebuild. **Not tested** via destroy.

### 26. EKS

Cluster recreation sequence in [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md): EKS → node group → add-ons → controllers → Argo.

After new cluster: kubeconfig/access entries, Argo repo registration, sync all Applications.

**Documented only** for full loss.

### 27. IAM

IAM roles for cluster, node group, LB controller, EBS CSI, pod identity — defined in Terraform.

**Recovery:** re-apply Terraform; verify trust policies and OIDC provider. **Access entries** for human operators must be recreated if account policy allows.

Credentials are **outside Git** — see [`business-continuity.md`](./business-continuity.md).

### 28. Add-ons

Inventory add-ons: `aws-ebs-csi-driver`, `coredns`, `eks-pod-identity-agent`, `kube-proxy`, `vpc-cni`. **`snapshot-controller`** pending install (**v8.6.0-eksbuild.8**).

Rebuild must reinstall add-ons before storage/snapshot drills work. Order documented in Terraform modules and recovery runbook.

---

## Part V — GitOps DR

### 29. Git

Repository: `kubernetes-platform-engineering-gitops` on GitHub (URL in runbooks — no tokens in docs).

| Protects | Risk |
|----------|------|
| All committed manifests, Terraform code, runbooks | Unpushed commits; branch deletion without remote |
| Revert history | GitHub outage blocks Argo fetch |

**Recovery:** clone from GitHub; secondary remote **TBD**. Local clones on workstation/Jenkins agent may serve short outages.

### 30. Argo Applications

AWS apps: `platform-lab-aws`, `platform-storage-aws`, `platform-security-aws`, `platform-observability-aws`, `platform-k8s-metrics-aws`. VMware: `platform-lab-local`, observability, storage, security, advanced lab sets.

Manifests under [`gitops/applications/`](../gitops/applications/). Disposable: **`platform-dr-recovery`**.

**Lab-tested:** normal sync operations. **Documented only:** Application delete recovery (**TBD**).

### 31. ApplicationSets

VMware only: cluster/env/list generators for advanced Argo labs. AWS: **none** at inventory.

Recovery: re-apply ApplicationSet YAML from Git; watch for cascading Application creation.

### 32. AppProjects

Projects enforce allow-lists (repos, namespaces, cluster resources). Loss → re-apply from Git before Applications sync.

**Lab-tested:** projects exist and confine apps (Section 23). **Documented only:** delete/recreate timing.

### 33. Jenkins

Jenkins builds image and **promotes digest to Git** — does not kubectl apply production apps.

| Outage impact | Recovery |
|---------------|----------|
| CI down | Running clusters unchanged; no new promotions |
| Restore | Docker Compose controller; restore creds from store; replay pipeline |

**Documented only** for outage drill. Architecture unchanged in Section 25 scope.

---

## Part VI — Recovery Exercises

### 34. Git recovery

**Exercise (planned):** bad ConfigMap in `dr-lab` → detect → `git revert` → Argo healthy.

**Status:** **Documented only** (**TBD**). **Related:** self-heal for live drift **lab-tested** on VMware.

### 35. Argo Application recovery

**Exercise:** delete `platform-dr-recovery` Application → re-apply YAML → Synced.

**Status:** **Documented only** (**TBD**). Runbook: [`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md).

### 36. Namespace recovery

**Exercise:** delete `dr-lab` namespace → Argo recreates.

**Status:** **Documented only** (**TBD**). **Never** on `storage-lab`.

### 37. EBS snapshot recovery

**Exercise:** install snapshot controller → `VolumeSnapshotClass` → snapshot → new PVC in `dr-storage-restore` → verify `state.txt` excludes post-snapshot writes.

**Status:** **Documented only** (**TBD**). Prerequisites in [`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md).

### 38. Node recovery

**Exercise (executed on AWS storage path):** terminate/replace worker in **same AZ** → CSI reattach → pod Ready.

**Status:** **Lab-tested** (~**6.3 min**). VMware node failure: **partially tested** (capacity/ingress path — [`vmware-node-failure-resilience.md`](./vmware-node-failure-resilience.md)).

### 39. Cluster rebuild model

**Exercise (not executed):** hypothetical new EKS from Terraform + Argo bootstrap + sync overlays + optional snapshot restore.

**Status:** **Documented only** — [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md), [`runbooks/aws-eks-disaster-recovery.md`](./runbooks/aws-eks-disaster-recovery.md).

---

## Part VII — Measurement

### 40. RPO measurement

1. Record **T_snap** (last known good snapshot or Git commit for config).
2. At failure, record **T_loss**.
3. **Demonstrated RPO** ≈ data changes between **T_snap** and **T_loss** (for config, compare Git SHA).

For `storage-demo`, without snapshots, only **live volume** exists — RPO for catastrophic volume loss is **total loss**.

### 41. RTO measurement

Define milestones: **T0** detect → **T1** decision → **T2** recovery action complete → **T3** verification pass (HTTP 200, `state.txt`, Argo Synced).

Record in incident notes (no secrets). Compare to targets in Part I §3.

### 42. Recovery evidence

Acceptable evidence in this project:

- Command transcripts in milestone docs (timestamps)
- Argo UI / `kubectl` outputs
- ALB health / curl checks
- EBS volume ID unchanged (same-volume path) or new volume ID (restore path)
- Git commit SHA of fix

Future: `platform-automate dr verify` (**planned** — Section 25).

### 43. Observability

Prometheus/Grafana/kube-state-metrics deployed via GitOps (`platform-lab-observability`, AWS observability app).

**Use in DR:** confirm `up`, pod Ready, ingress success **after** recovery. **Does not replace** restore — validates it ([`disaster-recovery-interview-notes.md`](./disaster-recovery-interview-notes.md) Q40).

Metrics history may be lost on namespace/cluster loss — config rebuilds from Git.

---

## Part VIII — Production

### 44. DR architecture

Production pattern (contrasted with lab): multi-AZ workers, **remote Terraform state**, **EBS snapshot schedules**, optional **AWS Backup for EKS**, **ECR mirror**, **GitHub Enterprise / mirror**, runbooks on-call, **regular restore drills**.

Lab intentionally stays cost-conscious and single-region — architecture docs here are **educational**, not deployed HA/DR tier.

### 45. Multi-AZ

Lab: subnets multi-AZ; app replicas can spread; **EBS lab volume single-AZ**. Production stateful: RDS Multi-AZ, EFS, or replicated systems — not proven in Project 1.

### 46. Multi-Region

Requires duplicated infra, data replication, DNS failover, runbook for overlay changes. **Documented only** in [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md).

### 47. Backup retention

Define retention per asset (snapshots 7/30/365 days, AWS Backup lifecycle, Git immortal). Lab: **no snapshot retention yet**. Delete **disposable** snapshots after evidence capture (Section 25 cost hygiene).

### 48. Security

- No credentials in Git, docs, reports, or diagrams.
- Rotate secrets after suspected compromise.
- RBAC least privilege; break-glass documented outside repo.
- DR drills must not paste kubeconfigs or `terraform.tfvars` into tickets.

See Phase 63 security review checklist in Section 25 mission (parent milestone).

### 49. Cost

Snapshots, AWS Backup storage, cross-region copies, standby clusters cost money. Lab: minimize disposable resources; **do not invent AWS prices** — use AWS Pricing Calculator when estimating.

Single NAT saves cost, reduces egress HA — document tradeoff in interviews.

### 50. Governance

Change control via PRs to `main`, Argo sync windows (if enabled), approval for destructive drills, inventory updates ([`dr-baseline-inventory.md`](./dr-baseline-inventory.md)) after major platform changes.

---

## Part IX — Runbooks

### 51. EKS recovery

Primary: [`runbooks/aws-eks-disaster-recovery.md`](./runbooks/aws-eks-disaster-recovery.md).

Flow: classify severity → read-only assess → identify failure domain → protect data → recover infra (Terraform) → recover GitOps → recover workloads → verify → post-incident.

### 52. EBS recovery

Primary: [`runbooks/ebs-storage-recovery.md`](./runbooks/ebs-storage-recovery.md).

Decision: same-volume (**lab-tested**) vs snapshot (**documented only**).

### 53. Git/Argo recovery

Primary: [`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md).

Covers bad commit revert, Application delete, namespace loss, Argo plane impairment, GitHub outage concepts.

### 54. Terraform recovery

Primary: [`runbooks/terraform-infrastructure-recovery.md`](./runbooks/terraform-infrastructure-recovery.md) + [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md).

Covers state backup, plan discipline, import vs greenfield, forward rebuild order.

**Adjacent (degradation, not full DR):** [`runbooks/aws-api-failure.md`](./runbooks/aws-api-failure.md), [`runbooks/kubernetes-api-failure.md`](./runbooks/kubernetes-api-failure.md), [`runbooks/automation-failure.md`](./runbooks/automation-failure.md).

---

## Part X — Interview

### 55. DR Interview Questions

Forty core questions with Project 1 answers: [`disaster-recovery-interview-notes.md`](./disaster-recovery-interview-notes.md).

Study order: fundamentals → scenario matrix → one runbook per recovery domain.

### 56. Scenario Questions

Use [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md) rows as flash cards:

- *Pod deleted vs namespace deleted vs cluster deleted* — recovery source changes completely.
- *EBS in wrong AZ* — not a bug; schedule to **1b** or snapshot-restore.
- *Argo Application deleted* — Git still has YAML; workloads may orphan.
- *Jenkins down* — runtime continues; promotion stops.

Always state **RPO/RTO**, **test status**, and **what is not recovered**.

### 57. Architecture Questions

Draw from memory:

```text
GitHub → Jenkins (build/promote digest) → Git main
Git main → Argo CD (VMware + AWS) → kubernetes/overlays/*
terraform/aws → VPC/EKS/add-ons/Argo bootstrap
EBS CSI → vol-05faa26874d720ecd (single AZ)
```

Explain **split ownership**: Terraform = cloud shell; Argo = app K8s; EBS = data; Git = config SoT.

Cite **local Terraform state** as the largest IaC DR gap in this lab.

Diagram: [`docs/diagrams/dr-dependency-graph.svg`](./diagrams/dr-dependency-graph.svg) (if present in repo).

---

## What happens if Project 1 loses everything?

This section answers the Section 25 **final engineering conclusion** using **actual recovery domains** for this lab — not generic cloud marketing.

### Assume total loss

**Total loss** means: workstation gone, local Terraform state gone, AWS account resources deleted (or account inaccessible), VMware VMs gone, Jenkins container gone, in-cluster Secrets gone — but **GitHub repo and Docker Hub digest remain** (worst-case: also lose GitHub — called out below).

### Recovery sequence (by domain)

| Step | Domain | Action | Project 1 source |
|------|--------|--------|------------------|
| 1 | **People / IAM** | Regain AWS account login; recreate IAM/access entries | Out-of-band; `API_AND_CONFIG_MAP` cluster needs access entries |
| 2 | **Git** | Clone repo; checkout known-good `main` SHA | GitHub |
| 3 | **Registry** | Pull `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` | Docker Hub |
| 4 | **Terraform** | `init/plan/apply` from [`terraform/aws`](../terraform/aws) — **new state** or restored state backup if any | Code in Git; state **not** in Git |
| 5 | **EKS platform** | VPC, cluster **1.36.4**, node group, add-ons including EBS CSI + **snapshot-controller v8.6.0-eksbuild.8** when added | Terraform |
| 6 | **Argo CD** | Helm release + bootstrap Application | Terraform + Git |
| 7 | **GitOps apps** | Sync `platform-lab-aws`, storage, security, observability apps | Git + Argo |
| 8 | **Stateless app** | Deployment comes back from overlay; verify ALB/ingress | **RPO 0** for committed config |
| 9 | **Stateful lab data** | **Only if** EBS snapshots or AWS Backup existed: restore to new volume/PVC in `dr-storage-restore` or recreate `storage-lab` | At inventory: **no snapshots** → **data not recoverable** |
| 10 | **Observability** | Redeploy from Git; empty TSDB | Config yes, history no |
| 11 | **Jenkins** | Recreate controller; restore credentials; pipelines from Git | [`business-continuity.md`](./business-continuity.md) |
| 12 | **VMware lab** | Rebuild VMs/kubeadm cluster; sync `platform-lab-local` | Manual rebuild **TBD**; Git for K8s config |
| 13 | **Verify** | Nodes Ready, Argo Synced, curl app, `state.txt` if storage restored, digest on pods | RTO **TBD** end-to-end |

### What is NOT automatically recovered

| Item | Why |
|------|-----|
| **`storage-demo` `state.txt`** on `vol-05faa26874d720ecd` | No snapshot at inventory; Git does not contain block data |
| **Terraform state** | Local, gitignored — without backup, import/reconcile burden or duplicate-resource risk |
| **Unpushed Git commits** | Never reached GitHub |
| **Jenkins / Argo / AWS credentials** | Not in Git by design |
| **Prometheus historical metrics** | Ephemeral TSDB unless separately backed up |
| **Manual console changes** | Never in Git/Terraform — drift or loss |
| **Argo UI-only tweaks** | Lost unless exported to Git ([`runbooks/git-argo-recovery.md`](./runbooks/git-argo-recovery.md) gap report) |
| **AWS Backup EKS recovery points** | **Not enrolled** at inventory |
| **DNS bookmarks** | ALB hostname changes on rebuild — update docs/runbooks |
| **VMware etcd / control-plane state** | No etcd backup in repo; single control-plane node |

### If GitHub is also lost

Recovery depends on **secondary remotes**, local clones, or GitHub org backup — **not configured in baseline**. Container image still on Docker Hub; **AWS and VMware clusters still require** a config source. This is a **configuration plane catastrophe** — runbooks cannot fix missing Git without a mirror.

### Master principle (restated)

Disaster recovery is **reconstruct + verify within RTO/RPO**, not merely possessing a backup file. For Project 1 today, the strongest recovery domains are **Git + registry + Terraform code**; the weakest are **EBS data without snapshots**, **local Terraform state**, and **single-node VMware control plane**.

---

## Embedded mastery checklist (Section 25)

| # | Topic | Can you explain? | Lab evidence |
|---|-------|------------------|--------------|
| 1 | HA vs DR | | Pod/node **tested**; cluster loss **not** |
| 2 | RPO for Git vs EBS | | Git **0** commit; EBS **undefined** |
| 3 | RTO for storage node fail | | **~6.3 min** |
| 4 | EBS AZ constraint | | **Tested** |
| 5 | Terraform vs Argo ownership | | README + [`terraform-dr.md`](./terraform-dr.md) |
| 6 | Local state risk | | **Documented** |
| 7 | AWS Backup gap | | [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) |
| 8 | Snapshot controller add-on | | **Adding** v8.6.0-eksbuild.8 |
| 9 | Safe DR namespaces | | `dr-lab`, `dr-storage-restore` |
| 10 | Runbook index | | Part IX above |

---

## Related reading (quick index)

- Fundamentals: [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md)
- Inventory: [`dr-baseline-inventory.md`](./dr-baseline-inventory.md)
- Scenarios: [`disaster-scenario-matrix.md`](./disaster-scenario-matrix.md)
- AWS Backup: [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md)
- Terraform DR: [`terraform-dr.md`](./terraform-dr.md)
- BC: [`business-continuity.md`](./business-continuity.md)
- Interview: [`disaster-recovery-interview-notes.md`](./disaster-recovery-interview-notes.md)
