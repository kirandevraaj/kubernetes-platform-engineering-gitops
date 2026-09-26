# Argo CD Interview Notes (Project 1)

Concise answers grounded in the **Kubernetes Platform Engineering & GitOps Lab**: VMware Argo CD `quay.io/argoproj/argocd:v3.5.3` on context `ckad-lab`, AWS Argo CD `v3.1.0` on EKS (context via `platform-aws-tools`), repo `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git`. Production-like apps (`platform-lab-local`, `platform-lab-aws`, storage/security/observability) are unchanged; advanced patterns live under AppProject `platform-advanced-lab` and namespaces `argo-advanced-*`, `argo-child-*`, `argo-nested-*`.

---

## 1. What is an AppProject?

An **AppProject** is Argo CD’s deployment policy object: which Git repos, cluster/namespace destinations, and Kubernetes resource kinds an Application may use. In Project 1, `platform-advanced-lab` allows only this repo, explicit lab namespaces plus `argocd` for child Apps/ApplicationSets, and a tight whitelist (Namespace, ConfigMap, Service, Deployment, Job, Application, ApplicationSet)—not `*`. Production apps use their own projects (`platform-lab`, `platform-lab-aws`, etc.) with matching boundaries.

## 2. What is a Sync Wave?

A **sync wave** is an ordering hint (`argocd.argoproj.io/sync-wave`) applied during the normal **Sync** phase. Lower numbers run first (e.g. ConfigMap `-1`, Service `0`, Deployment `1`). Child Applications in `platform-app-of-apps` use waves `-1`, `0`, `1` for config → service → workload. Waves do not replace hooks; they order resources within a phase.

## 3. What is a Hook?

A **hook** is a resource (here, a Job) annotated with `argocd.argoproj.io/hook` (`PreSync`, `PostSync`, `SyncFail`, etc.) so Argo CD runs it at a specific point in the sync lifecycle, outside normal long-lived manifest management. Lab examples: `argo-pre-sync-check`, `argo-post-sync-check` in `kubernetes/argo-advanced-lab/hooks/`.

## 4. Difference between Hook and Wave?

**Phase/hook** answers *when in the lifecycle* (before sync, after sync, on failure). **Wave** answers *in what order* among peers in the same phase. You can combine them (e.g. PostSync hook at wave `2` after Deployment at wave `1`). Hooks are often Jobs with delete policies; waves apply to any resource type in the sync operation.

## 5. What is ApplicationSet?

**ApplicationSet** is a controller that generates one or more **Application** objects from **generators** (list, Git directories, clusters, etc.) plus a **template**. Project 1 examples: `platform-advanced-set` (list → `argo-advanced-dev/test/stage`), `platform-advanced-env-set`, `platform-advanced-cluster-set`, `platform-nested-list-set` (via App-of-ApplicationSets).

## 6. Application vs ApplicationSet?

An **Application** declares a single desired deployment (one source path → one destination). An **ApplicationSet** declares *how to mint* many Applications from parameters. You still sync workloads through each generated Application; the Set is meta-GitOps for scale and consistency.

## 7. What is App-of-Apps?

**App-of-Apps** is a parent **Application** whose manifest directory contains other **Application** YAML files. Parent `platform-app-of-apps` syncs `kubernetes/argo-app-of-apps/children` into namespace `argocd`; children (`app-child-config`, `app-child-service`, `app-child-workload`) each sync their own workload paths— the parent does not apply Deployments directly.

## 8. Why use ApplicationSet instead of manually creating Applications?

When the same template repeats across environments, clusters, or repo paths—three envs from one list, directories discovered by Git generator—ApplicationSet avoids copy-paste drift and centralizes naming, project, and sync policy. Manual Applications remain right for one-off production apps like `platform-lab-local` and `platform-lab-aws`.

## 9. What happens when an ApplicationSet input disappears?

If a list/Git element is removed, the controller treats the corresponding Application as **not desired**; with owner references and prune policies, generated Apps can be deleted (lab validates on `dev`/`test`/`stage` only). This is GitOps lifecycle: shrinking generator input shrinks the Application fleet—never tested on production Applications.

## 10. How do you restrict ApplicationSet security?

Hard-code or tightly template `project: platform-advanced-lab` (never `default` or `*`), narrow generators (explicit list paths, labeled cluster selector—not `{}`), use `goTemplateOptions: [missingkey=error]`, restrict who can create ApplicationSets via Argo RBAC, and keep AppProject `sourceRepos`/`destinations`/`namespaceResourceWhitelist` minimal. Broad generators + weak projects enable privilege escalation.

## 11. How do Sync Windows work?

**Sync windows** on an AppProject (or app) allow or deny automated/manual sync during schedules (cron, duration, timezone). They control **when** sync may run—orthogonal to **what/where** (AppProject) and **who** (RBAC). Lab project keeps `syncWindows: []`; temporary deny windows may be used only on advanced lab apps during validation, then removed.

## 12. What is PruneLast?

**PruneLast=true** defers pruning until after other resources in the sync succeed, reducing the chance of deleting a dependency still needed during apply. Used on `platform-argo-advanced-lab` alongside `CreateNamespace`, `ApplyOutOfSyncOnly`, and `ServerSideApply`—not enabled globally on all production apps.

## 13. What is ApplyOutOfSyncOnly?

**ApplyOutOfSyncOnly=true** limits the sync operation to resources that differ from Git, reducing API churn and accidental contention. All Project 1 production-like Applications and advanced lab apps use it; it pairs well with automated sync and self-heal.

## 14. What is the danger of Replace/Force?

**Replace** and **Force** sync options can recreate resources aggressively (dropping fields managed outside Git, causing brief outages or data loss on StatefulSets/PVCs). Project 1 documents them in `kubernetes/argo-advanced-lab/sync-options/notes.yaml` but **does not** apply them to `platform-lab-local`, `platform-lab-aws`, or other production-like workloads.

## 15. How do you order CRD → CR deployment?

Use **sync waves**: CRD at low wave (e.g. `-2`), CR at `-1`, controller/workload at `0+`. Ensure CRD is healthy before CR sync; for operators, often separate Applications (CRDs first, then bundle) or hooks for validation. Lab demonstrates wave ordering on ConfigMap/Service/Deployment, not CRDs in production.

## 16. How do you prevent recursive App-of-Apps?

Parent Application path must not include a manifest that points back to the parent or creates a cycle (parent → child → parent). Keep child sources as workload dirs only; do not nest `platform-app-of-apps` under its own children. ApplicationSet templates must not generate an Application that manages the Set itself. Project 1 verifies no self-referential paths in `gitops/applications/` and nested sets.

## 17. How would you design dev/stage/prod?

Separate **Applications or ApplicationSets** per environment with distinct namespaces, overlays (`kubernetes/overlays/local` vs `aws`), and AppProjects; promote **immutable artifacts** (image digest) via Git commits, not kubectl. Project 1 already splits `platform-lab-local` vs `platform-lab-aws` on **separate Argo instances**; advanced lab simulates envs with `platform-advanced-set` and `platform-advanced-env-set` without replacing those apps.

## 18. Where should Jenkins end and Argo CD begin?

**Jenkins**: build, test, publish image to Docker Hub, commit overlay tag/digest to Git (CI + promotion). **Argo CD**: read Git, render (Kustomize/Helm), apply to cluster, prune, self-heal (CD). Jenkins never runs `kubectl apply` on app namespaces in this lab; Argo never builds images. Boundary is the Git commit that updates desired state.

## 19. Why should Git remain the source of truth?

Auditability, rollback via revert, consistent drift detection, and separation of CI artifact production from CD reconciliation. Self-heal on `platform-lab-local` restores live patches to Git; manual cluster edits are temporary. ApplicationSet and App-of-Apps still resolve to Git paths on `main`.

## 20. How do you troubleshoot an Application stuck in Progressing?

Check **resource tree** and **sync operation** in UI/CLI: failing hooks, unhealthy workloads, sync waves blocked on unhealthy deps, project denial, or sync window deny. Inspect `argocd app get <name>`, controller logs, hook Jobs, and events. For image issues, confirm Git tag/digest matches registry (`platform-lab` stays `0.1.4` / `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`). Refresh/hard refresh if commit lag; avoid Force on production.

---

**Related docs:** [argo-advanced-patterns.md](./argo-advanced-patterns.md) · [architecture/argo-gitops-reference.md](./architecture/argo-gitops-reference.md)
