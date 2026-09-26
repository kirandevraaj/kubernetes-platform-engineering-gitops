# AWS EKS Disaster Recovery Runbook (Project 1 — Section 25)

**Scope:** AWS lab only — cluster `platform-lab-aws-lab-eks`, context `platform-lab-aws`, region `ap-south-1`, VPC `vpc-00c54a2d05f84fed6`.  
**Out of scope:** Using **`terraform destroy`** or deleting the main cluster/VPC as a “DR test.”  
**Companion docs:** [`disaster-scenario-matrix.md`](../disaster-scenario-matrix.md), [`terraform-recovery-runbook.md`](../terraform-recovery-runbook.md), [`aws-backup-eks-dr.md`](../aws-backup-eks-dr.md).

---

## Trigger Conditions

Use this runbook when one or more of the following persist and user-facing or platform-lab capability is impaired:

- EKS API unreachable or consistently failing (`kubectl`, Argo, automation).
- All or most worker nodes **NotReady**; workloads cannot schedule or stay Ready.
- Regional/AZ impairment affecting subnets, NAT, or ALB targets for the platform.
- Confirmed data loss or corruption on EBS-backed lab storage (`storage-lab`).
- GitOps plane down (Argo CD unavailable) **and** configuration drift or failed deployments block recovery.
- Operator error: namespace/Application deletion on **non-disposable** namespaces (escalate immediately).

**Do not use for:** single pod delete, single pod NotReady with healthy peers, or routine Argo OutOfSync fixed by Git push.

---

## Severity Classification

| Severity | Definition | Examples in this lab | Initial response |
|----------|------------|----------------------|------------------|
| **SEV-3** | Degraded; core apps partially available | One `platform-lab` pod down; one ingress target unhealthy | Follow targeted runbooks; no infra rebuild |
| **SEV-2** | Major feature unavailable; data at risk | All app pods down; ALB unhealthy; Argo sync failing | Protect data; GitOps + storage runbooks |
| **SEV-1** | Cluster or region platform loss | Cluster deleted; API hard down; AZ-wide impairment | Terraform rebuild model + restore data plane |
| **SEV-0** | Account compromise / data exfiltration | Out of lab scope — invoke security IR | Isolate credentials; AWS support |

Record severity in the incident log with UTC timestamps.

---

## Initial Assessment

1. **Confirm context:** `kubectl config use-context platform-lab-aws` (via `platform-aws-tools` if applicable).
2. **Read-only cluster snapshot:**
   - `kubectl get nodes`
   - `kubectl get ns`
   - `kubectl get applications.argoproj.io -n argocd`
   - `kubectl get pvc,pv -A`
3. **AWS read-only:** `aws eks describe-cluster --name platform-lab-aws-lab-eks --region ap-south-1` (no credential output in tickets).
4. **Check failure domain:** application vs node vs AZ vs control plane vs Git/registry vs Terraform/AWS account.
5. **Freeze risky changes:** no volume deletes, no cluster delete, no mass prune.

---

## Identify Failure Domain

| Symptom | Likely domain | Next doc |
|---------|---------------|----------|
| Pods Pending / PVC not bound | Storage / CSI / AZ | [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) |
| ImagePullBackOff | Registry / NAT egress | [`business-continuity.md`](../business-continuity.md) (registry) |
| Argo SyncError / repo fetch | GitHub / repo creds | [`git-argo-recovery.md`](./git-argo-recovery.md) |
| 503 from ALB | Ingress / targets / nodes | [`kubernetes-api-failure.md`](./kubernetes-api-failure.md) |
| Terraform plan drift / state missing | IaC | [`terraform-infrastructure-recovery.md`](./terraform-infrastructure-recovery.md) |
| Only `storage-demo` affected | EBS / same-AZ | [`aws-storage-resilience.md`](../aws-storage-resilience.md) |

---

## Protect Remaining Data

**Before** destructive recovery steps:

1. **EBS lab volume** `vol-05faa26874d720ecd` (`data-storage-demo-0`, AZ `ap-south-1b`): do **not** delete. If snapshot controller exists, take a **VolumeSnapshot** before invasive changes (Section 25 drill uses markers `SNAPSHOT-POINT-A/B` in disposable restore path only).
2. **Stop writes** to corrupted volumes if overwrite suspected; snapshot if possible.
3. **Export incident timeline** (T0 failure detection) for RTO/RPO — do not store secrets in notes.
4. **Git:** do not force-push `main`; prefer revert commits for bad config.
5. **Terraform:** copy `terraform.tfstate` + `.backup` if state still accessible ([`terraform-dr.md`](../terraform-dr.md)).

---

## Recover Infrastructure

When VPC/cluster/node groups are missing or unrecoverable:

1. Follow [`terraform-recovery-runbook.md`](../terraform-recovery-runbook.md) **forward rebuild** order: IAM → VPC/NAT → EKS → node group → add-ons (including `aws-ebs-csi-driver`) → LB controller → metrics-server → Argo CD Helm → GitOps bootstrap.
2. Run from canonical workspace (`platform-aws-tools`) with **local state** until remote backend is adopted.
3. **`terraform plan`** must be reviewed before **`apply`** — never use destroy as DR.
4. **Auth mode** remains `API_AND_CONFIG_MAP`; restore access entries / kubeconfig access without publishing secrets in docs.
5. **Observed rebuild duration:** **TBD** (not safely measured on live cluster).

If infrastructure exists but state is lost, see [`terraform-infrastructure-recovery.md`](./terraform-infrastructure-recovery.md) import vs greenfield decision.

---

## Recover Storage

| Case | Procedure |
|------|-----------|
| Pod deleted; PVC intact | StatefulSet recreates pod; CSI reattaches same EBS (**Tested**, ~14 s Ready on pod delete) |
| Worker lost, same AZ capacity | Scheduler + CSI reattach (**Tested**, ~6.3 min T0→Ready) |
| Data loss / need point-in-time | Snapshot → new PVC in `dr-storage-restore` — [`ebs-storage-recovery.md`](./ebs-storage-recovery.md) (**Documented only** until drill completes) |
| AWS Backup EKS restore | Only if enrolled; at inventory **no EKS protected resources** — [`aws-backup-eks-dr.md`](../aws-backup-eks-dr.md) |

StorageClass for lab: `ebs-gp3`. Original volume ID: `vol-05faa26874d720ecd`.

---

## Recover Kubernetes State

1. **Managed control plane:** AWS operates EKS CP HA — do not simulate CP destruction. Verify cluster ACTIVE and endpoint reachable.
2. **etcd object loss (namespace/app):** Prefer **Git + Argo** over manual object recreation for owned apps.
3. **CRDs / add-ons:** Reconcile via Terraform EKS add-ons (EBS CSI present; snapshot controller **TBD** at inventory).
4. **RBAC:** Restore from Git overlays where declared; do not grant cluster-admin as default DR step ([`security-rbac.md`](../security-rbac.md)).
5. **AWS Backup** (optional future): non-destructive restore to existing/new cluster per AWS docs — **not executed** in lab inventory.

---

## Restore GitOps

1. Ensure Argo CD pods Ready in `argocd` namespace (reinstall via Terraform if missing).
2. Verify Application objects exist for `platform-lab-aws`, `platform-storage-aws`, observability apps — sources under `kubernetes/overlays/aws` and `gitops/`.
3. For lost Application CR only: re-apply from Git (`gitops/applications/`) or Terraform bootstrap — [`git-argo-recovery.md`](./git-argo-recovery.md).
4. Sync policy: production-like apps use automated sync + self-heal where configured; use **disposable** `platform-dr-recovery` / `dr-lab` for DR drills.
5. Confirm image digest in Git: `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` (`0.1.4`).

---

## Restore Application

1. Argo sync `platform-lab-aws` → Deployment 2/2 Ready, Service, Ingress, HPA, PDB, NetworkPolicy per overlay.
2. Validate HTTP via ALB / documented URL; `/health` and metrics if observability enabled.
3. **storage-lab:** `platform-storage-aws` → `storage-demo-0` Bound to `data-storage-demo-0`; verify `state.txt` on live volume (do not destroy original).
4. **security-lab / observability:** sync respective Applications; Grafana/Prometheus targets green.
5. Jenkins **does not** deploy — if new image needed, restore Jenkins first, then promote via Git.

---

## Restore Observability

1. Sync Argo apps for AWS observability stack (lightweight or full per lab config).
2. Confirm kube-state-metrics, node metrics, cAdvisor scrapes.
3. Dashboards: `platform-lab-aws-lightweight`, storage dashboard for `data-storage-demo-0`.
4. Use observability to **validate** recovery (targets up, error rate normal) — TSDB history RPO **TBD** (not backed up in lab).

---

## Validate

Minimum post-recovery checklist:

| Check | Command / signal | Pass criteria |
|-------|------------------|---------------|
| Nodes | `kubectl get nodes` | All Ready (or documented toleration) |
| Core app | `kubectl -n platform-lab get deploy,pods,ingress` | 2/2 Ready; ingress has healthy targets |
| GitOps | `kubectl -n argocd get applications` | Synced / Healthy |
| Storage | `kubectl -n storage-lab get pvc,pod` | PVC Bound; pod Ready |
| EBS CSI | `kubectl -n kube-system get pods -l app.kubernetes.io/name=aws-ebs-csi-driver` | Controllers Ready |
| ALB | AWS console or `kubectl describe ingress` | Active targets |
| Image | Deployment spec | Digest matches Git pin |

Future automation: `platform-automate dr verify` (**planned** in Section 25).

---

## Measure RTO/RPO

Record UTC timestamps:

| Marker | Meaning |
|--------|---------|
| T0 | Incident start / detection |
| T1 | Failure domain identified |
| T2 | Recovery action started |
| T3 | Data plane protected (snapshot, etc.) |
| T4 | Workloads Ready |
| T5 | User-visible validation pass |

- **RTO (observed)** = T5 − T0 (or T4 − T0 for internal service).
- **RPO (observed)** = data loss window for stateful tier (last snapshot vs failure time).

**Lab OBSERVED examples (not full DR):** same-AZ node failure **≈ 6.3 min** to pod Ready; pod delete **~14 s**. Full cluster RTO **TBD**.

---

## Close Incident

1. Document timeline, severity, root cause, and recovery path used.
2. Remove temporary resources (extra node groups, `dr-storage-restore`, test snapshots) per cleanup phase.
3. Confirm main EKS, VPC, `vol-05faa26874d720ecd`, and production-like namespaces intact.
4. Update [`disaster-scenario-matrix.md`](../disaster-scenario-matrix.md) **Observed** column if new evidence.
5. Communicate: service restored; any residual risk (e.g., no snapshot yet).

---

## Postmortem

Template (blameless):

1. **Impact:** who/what was affected, duration, data loss if any.
2. **Timeline:** T0–T5 from above.
3. **Root cause:** technical and process gaps.
4. **What worked:** GitOps, CSI reattach, runbooks used.
5. **What did not:** missing snapshots, local Terraform state, single NAT, etc.
6. **Action items:** with owners — e.g., remote state, snapshot schedule, `dr-lab` drill cadence, AWS Backup enrollment decision.
7. **Production delta:** what would differ in real prod (multi-region, ECR mirror, SRE on-call).

---

## Related runbooks

- [`ebs-storage-recovery.md`](./ebs-storage-recovery.md)
- [`git-argo-recovery.md`](./git-argo-recovery.md)
- [`terraform-infrastructure-recovery.md`](./terraform-infrastructure-recovery.md)
- [`aws-api-failure.md`](./aws-api-failure.md)
