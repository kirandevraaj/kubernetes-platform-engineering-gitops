# Git and Argo CD Recovery Runbook (Project 1 — Section 25)

**Principle:** **Git** is the source of truth for desired configuration. **Argo CD** is the reconciliation engine — not a backup of Git history.  
**Instances:** VMware Argo CD **v3.5.3** (`ckad-lab`); AWS Argo CD **v3.1.0** (`platform-lab-aws`).  
**Repository:** `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git` (no credentials in this doc).  
**Safe DR drills:** Application `platform-dr-recovery`, namespace `dr-lab` only. **Never** use production apps (`platform-lab-local`, `platform-lab-aws`, `platform-storage-aws`, etc.) for destructive delete tests.

---

## Trigger Conditions

- Argo Application missing but workloads still running.
- Namespace deleted (accidental or drill).
- Git `main` contains bad config (merged mistake).
- Argo UI/API down; sync stalled.
- ApplicationSet or AppProject deleted or corrupted.
- GitHub unreachable (cannot fetch; local clone may still exist).

---

## Severity and Scope

| Event | Typical severity | Disposable scope |
|-------|------------------|------------------|
| Bad commit on `dr-lab` | Low | Revert in Git |
| `platform-dr-recovery` Application deleted | Low | Re-apply from Git |
| `dr-lab` namespace deleted | Medium | Argo recreate with `CreateNamespace=true` |
| Bad commit on `platform-lab-aws` overlay | High | Revert + sync; no delete test |
| Argo CD namespace impaired | High | Helm/Terraform reinstall |
| GitHub long outage | High | Cached repo / mirror |

---

## Git Corruption / Bad Desired State

**Symptoms:** Argo Synced but wrong behavior; or OutOfSync after intentional bad push.

**Recovery:**

1. Identify authoritative commit (last known good SHA on `main`).
2. **Revert** bad commit(s) on `main` (preferred) or restore file from history — do not leave hotfix only on cluster.
3. Push to GitHub; wait for Argo poll/webhook (VMware/AWS poll intervals per app).
4. Observe: OutOfSync → sync → Synced/Healthy.
5. Measure T0 (push) → T2 (resource corrected) — **TBD** on `dr-lab` drill.

**What Git restores:** Deployments, Services, ConfigMaps, Ingress, HPA, PDB, NetworkPolicy, Application/AppProject YAML in repo.  
**What Git does not restore:** EBS `state.txt`, ephemeral pod memory, Terraform state, Jenkins credentials, container image bytes (registry separate).

**Test status:** Argo self-heal for **live drift** **Tested** on VMware (~sub-second detect in annotation revert experiment — [`vmware-argo-self-healing.md`](../vmware-argo-self-healing.md)). Full bad-commit revert on `dr-lab` **Documented only** (**TBD**).

---

## Argo Application Deletion

**Symptoms:** `kubectl get application -n argocd` missing entry; workloads may still exist.

**Mechanism:**

- Deleting the **Application** CR removes Argo tracking metadata, not necessarily child resources (depends on finalizers and `--cascade` behavior).
- **Git remains**; manifests under `gitops/applications/` and `kubernetes/` unchanged.

**Recovery (disposable app):**

1. Re-apply Application manifest, e.g. [`gitops/applications/platform-dr-recovery.yaml`](../../gitops/applications/platform-dr-recovery.yaml).
2. Or Terraform GitOps bootstrap if platform bootstrap Application was lost.
3. Sync; verify Synced/Healthy and resources in `dr-lab`.

**Production-like apps:** Re-apply from Git mirror; never delete as a test.

**Test status:** **Documented only** (**TBD** timing for `platform-dr-recovery`).

---

## Namespace Loss

**Symptoms:** `kubectl get ns dr-lab` NotFound; Argo reports missing resources.

**Recovery:**

1. Confirm namespace was **disposable only** (`dr-lab` — no platform-lab resources).
2. Ensure Application sync option **`CreateNamespace=true`** (lab DR app).
3. Trigger sync or wait for automated sync.
4. Verify recreation: Namespace, ConfigMap `dr-recovery-marker`, Service, Deployment, Pods Ready.

**Does not restore:** Any data not defined in Git (none for stateless dr-lab); external AWS resources; secrets not in Git (use sealed-secrets/external secrets pattern in prod).

**Test status:** **Documented only** (**TBD** T0–T4 timings).

---

## ApplicationSet Loss

**Lab context:** Advanced patterns under `gitops/appsets/` and AppProject `platform-advanced-lab` — **not** production apps.

**Recovery:**

1. Re-apply ApplicationSet YAML from Git (e.g. `platform-advanced-env-set.yaml`).
2. Reconcile generated Applications.
3. Verify generator parameters (Git directories, clusters) unchanged.

**If Git lost:** ApplicationSet definitions lost unless recovered from clone/backup — Argo cannot invent Git history.

**Test status:** **Documented only** (no destructive test on advanced lab required for Section 25 matrix).

---

## AppProject Loss

**Symptoms:** Applications fail validation; sync denied.

**Recovery:**

1. Re-apply AppProject from `gitops/projects/` (e.g. `platform-dr-recovery.yaml`, `platform-lab-aws.yaml`).
2. Ensure `sourceRepos` and `destinations` match lab boundaries.
3. Re-sync dependent Applications.

**Gap report (Section 25):** Anything configured only in Argo UI/live and not in Git must be exported manually to Git in a **non-secret** form — do not paste repo passwords or private keys into docs.

---

## Argo CD Platform Failure (controller unavailable)

**Not safe to test** by deleting `argocd` namespace on live AWS lab.

**Recovery model:**

1. Fix Kubernetes (nodes, API) first — [`aws-eks-disaster-recovery.md`](./aws-eks-disaster-recovery.md).
2. Reinstall Argo via Terraform Helm release in `terraform/aws`.
3. Re-register repository connection using **secure credential store** (K8s Secret created out-of-band — **do not commit**).
4. Re-apply AppProjects and Applications from Git.
5. Sync all apps; validate production-like health.

**Test status:** **Documented only**.

---

## GitHub Unavailable

**Symptoms:** Argo `ComparisonError` / repo fetch failures; Jenkins cannot poll.

**Recovery:**

1. Confirm outage (status.github.com); avoid uncommitted cluster-only fixes becoming SoT.
2. Use **local clone** on operator machine for read/revert prep; push when GitHub returns.
3. Argo may serve last cached commit — **no new sync** until repo reachable.
4. Long term: secondary remote mirror, enterprise Git HA.

**Test status:** **Not safe to test in lab** (blocks all GitOps).

---

## Jenkins Interaction

Jenkins promotes image tags/digests to Git; it **does not** deploy. If Jenkins is down, recovery of **running** clusters is unaffected; new promotions wait. See [`disaster-recovery-fundamentals.md`](../disaster-recovery-fundamentals.md) Section Jenkins DR.

---

## Validation Checklist

| Check | Pass |
|-------|------|
| `kubectl -n argocd get applications` | Target apps Synced/Healthy |
| `kubectl -n dr-lab get all` | DR drill resources present (if enabled) |
| Git SHA on Argo app status | Matches intended `main` |
| No secret values in Application spec in docs/logs | Verified |
| Image digest | `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |

---

## Related

- [`../architecture/gitops-flow.md`](../architecture/gitops-flow.md)
- [`../argo-cd-interview-notes.md`](../argo-cd-interview-notes.md)
- [`aws-eks-disaster-recovery.md`](./aws-eks-disaster-recovery.md)
- Diagram: [`../diagrams/disaster-recovery-architecture.svg`](../diagrams/disaster-recovery-architecture.svg)
