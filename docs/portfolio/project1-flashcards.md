# Project 1 — Flashcards

Short Q/A cards drawn from Project 1 evidence. Each answer names the document that proves it. Cover the answer, say it out loud, then check.

Numbers are lab observations, not SLAs. "Historical" means the environment no longer runs (see [project1-environment-map.md](./project1-environment-map.md)).

---

## Kubernetes

**Q: What is the difference between Running and Ready?**
A: Running means the container process started. Ready means the readiness probe passes, so the pod is listed in Service endpoints. In the readiness lab a paused container stayed Running but went NotReady at ~31.5 s and left the endpoints. — [vmware-pod-self-healing.md](../vmware-pod-self-healing.md)

**Q: When one pod was deleted, what brought it back, and how fast?**
A: The ReplicaSet, not HPA, PDB or Argo. The replacement was Ready in ~10.4 s and `/health` stayed 200 throughout. — [vmware-pod-self-healing.md](../vmware-pod-self-healing.md)

**Q: A failed readiness probe: does the ReplicaSet create a new pod?**
A: No. The pod stays; it only leaves the endpoints. Liveness may restart the same container (restartCount went 0 → 1). — [vmware-pod-self-healing.md](../vmware-pod-self-healing.md)

**Q: Why were no replacement pods created during the 5-minute worker outage?**
A: The default `unreachable:NoExecute` toleration is 300 s. Pods are not evicted until it expires. — [vmware-node-failure-resilience.md](../vmware-node-failure-resilience.md)

**Q: Does a PodDisruptionBudget protect against a node crash?**
A: No. A PDB limits voluntary disruptions (drain, eviction), not involuntary failures. — [architecture/reliability.md](../architecture/reliability.md)

**Q: What rollout settings kept 0.1.4 serving while 0.1.5 was broken?**
A: RollingUpdate `maxSurge: 1`, `maxUnavailable: 0`, plus a readiness probe on `/health`. The new pod never became Ready, so the old pods were never removed. — [vmware-rollout-failure-rollback.md](../vmware-rollout-failure-rollback.md)

**Q: What did Kustomize give Project 1?**
A: One `kubernetes/base` and small `overlays/local` and `overlays/aws` differences (image digest, ingress, HPA/PDB patches). — [adr/005-kustomize-for-environment-overlays.md](../adr/005-kustomize-for-environment-overlays.md)

**Q: What was the node's Ready condition after the kubelet stopped?**
A: `Unknown` (not `False`) at ~42.7 s, with `unreachable:NoSchedule` then `unreachable:NoExecute` taints. — [vmware-node-failure-resilience.md](../vmware-node-failure-resilience.md)

## GitOps / CI/CD

**Q: Who deploys in Project 1: Jenkins or Argo CD?**
A: Argo CD. Jenkins tests, builds, pushes, captures the digest and commits it to Git. It never runs `kubectl apply`. — [adr/003-gitops-with-argo-cd.md](../adr/003-gitops-with-argo-cd.md)

**Q: Which files does the Jenkins promotion commit touch?**
A: Only `kubernetes/overlays/local/kustomization.yaml` and `kubernetes/overlays/aws/kustomization.yaml` (digest + version label). — [../../jenkins/README.md](../../jenkins/README.md)

**Q: Why doesn't the promotion commit trigger an endless build loop?**
A: The Detect Application Change stage only sets `APP_CHANGED=true` for `app/` paths. Overlay-only commits run and skip every later stage. — [architecture/ci-cd-flow.md](../architecture/ci-cd-flow.md)

**Q: Tag vs digest?**
A: The tag (`0.1.4`) names the logical release and can be moved. The digest (`sha256:1cca2b59...872ff`) identifies the immutable artifact. Project 1 pins digests. — [adr/004-immutable-image-digest-promotion.md](../adr/004-immutable-image-digest-promotion.md)

**Q: How was the bad 0.1.5 release rolled back?**
A: With Git: `302a506` re-pinned the 0.1.4 digest in both overlays and `95820c8` reverted the app source. Argo reconciled (~6 s). No `kubectl rollout undo`. — [vmware-rollout-failure-rollback.md](../vmware-rollout-failure-rollback.md)

**Q: Why did the first Argo drift test fail?**
A: A live-only annotation is not a field Git manages, so Argo never saw drift (~180 s, still Synced). Changing a Git-managed label healed in under a second. — [vmware-argo-self-healing.md](../vmware-argo-self-healing.md)

**Q: Can an Argo Application be Synced and Degraded at once?**
A: Yes. During 0.1.5 the live spec matched Git (Synced) but the new pod never became Ready (Degraded). — [vmware-rollout-failure-rollback.md](../vmware-rollout-failure-rollback.md)

**Q: ApplicationSet vs App-of-Apps?**
A: An ApplicationSet generates Applications from a generator (List, Git, Cluster). App-of-Apps is a parent Application whose manifests are child Applications. Neither replaces AppProject security. — [argo-advanced-patterns.md](../argo-advanced-patterns.md)

**Q: What caused the `waves-health` ComparisonError?**
A: Kustomize could not resolve `../base/namespace.yaml`, so Argo could not generate manifests (Unknown). Fix: a self-contained kustomization. — [postmortems/argo-comparison-error.md](../postmortems/argo-comparison-error.md)

**Q: Why could Argo CD v3.5.3 not apply the ingress HA patch at first?**
A: It rejected `ServerSideApply` combined with `Force`. Fix: manage the full Deployment manifest without Force. — [vmware-ingress-ha.md](../vmware-ingress-ha.md)

## AWS (historical runtime)

**Q: What did Terraform build?**
A: VPC `10.50.0.0/16` over 2 AZs with a single NAT, EKS 1.36, IAM, AWS Load Balancer Controller, Metrics Server, Argo CD + GitOps bootstrap, EBS CSI and the snapshot controller. — [../../terraform/aws/README.md](../../terraform/aws/README.md)

**Q: Why were nodes moved from t3.small to t3.medium?**
A: Pod density. t3.small allowed 11 pods per node (22 total, ~4 free), too few for observability. t3.medium allows 17 per node. — [aws-observability-capacity-analysis.md](../aws-observability-capacity-analysis.md)

**Q: What does ALB target-type `ip` mean?**
A: The ALB sends traffic straight to pod IPs, with no NodePort or in-cluster ingress controller hop. — [adr/007-aws-alb-vs-vmware-ingress.md](../adr/007-aws-alb-vs-vmware-ingress.md)

**Q: What was left Degraded at portfolio freeze, and why was it not "fixed"?**
A: `platform-observability-aws`: a Grafana surge pod was Pending (`Too many pods`) while the serving pod stayed Ready. Scaling nodes was out of scope, so it was recorded as a limitation. — [aws-observability-degraded-final-state.md](./aws-observability-degraded-final-state.md)

**Q: Is the AWS environment running now?**
A: No. It was destroyed on 2026-09-26. Terraform state is empty. It can be rebuilt from source, but that rebuild was not run after teardown. — [operations/aws-lab-teardown.md](../operations/aws-lab-teardown.md)

**Q: IAM vs Kubernetes RBAC?**
A: IAM controls AWS APIs; RBAC controls kube-apiserver verbs. They meet in chains like EBS CSI: Pod → ServiceAccount → Pod Identity → IAM Role → EBS APIs. — [security-rbac.md](../security-rbac.md)

## Observability

**Q: Metrics Server vs Prometheus?**
A: Metrics Server serves live resource metrics for `kubectl top` and HPA. Prometheus scrapes and stores time series for dashboards. Fixing Prometheus does not fix HPA. — [vmware-observability-anatomy.md](../vmware-observability-anatomy.md)

**Q: KSM vs node-exporter?**
A: kube-state-metrics reports Kubernetes object state (replicas, pod ready, PVC phase). node-exporter reports host metrics (CPU, memory, disk) per node. — [adr/006-prometheus-grafana-observability.md](../adr/006-prometheus-grafana-observability.md)

**Q: Why did PVC/PV phase panels need extra work on AWS?**
A: The KSM `persistentvolumeclaims` / `persistentvolumes` collectors had to be enabled. — [aws-storage-statefulset.md](../aws-storage-statefulset.md)

**Q: How did the app expose metrics?**
A: `/metrics` via `prometheus-fastapi-instrumentator` (from 0.1.3), scraped every 30 s by a ServiceMonitor on VMware. — [architecture/observability.md](../architecture/observability.md)

**Q: Why were 6 VMware targets DOWN on the platform dashboard?**
A: Control-plane scrape targets (controller-manager, scheduler, etcd, kube-proxy) bound locally. Recorded as lab noise, not an app problem. — [grafana-platform-dashboard.md](../grafana-platform-dashboard.md)

**Q: Why can a 30 s scrape interval hide an outage?**
A: A dip shorter than the interval may never be sampled. The pod-delete dip needed a cordoned experiment to become visible. — [vmware-pod-self-healing.md](../vmware-pod-self-healing.md)

## Networking

**Q: What was the VMware external request path?**
A: Client → MetalLB VIP `192.168.56.200:80` → ingress-nginx → Ingress `platform-lab.local` → Service `platform-lab:8000` → pod. — [architecture/networking.md](../architecture/networking.md)

**Q: Why did external requests return `000` during the worker-02 outage?**
A: The only ingress-nginx replica ran on worker-02. MetalLB re-announced the VIP from worker-01, but there was no ingress backend. — [vmware-networking-anatomy.md](../vmware-networking-anatomy.md)

**Q: What removed the ingress SPOF?**
A: 2 ingress-nginx replicas, soft topology spread, PDB `minAvailable: 1`, all managed through GitOps. Each worker-loss test gave 75 OK / 0 FAIL. — [vmware-ingress-ha.md](../vmware-ingress-ha.md)

**Q: Does NetworkPolicy always work?**
A: Only if the CNI enforces it. Calico on VMware blocked the denied client (timeout). On AWS VPC CNI the denied client still got `OK`. — [security-rbac.md](../security-rbac.md)

**Q: What was the Calico and kube-proxy setup?**
A: Calico v3.30.7, pod pool `10.244.0.0/16`, VXLAN CrossSubnet; kube-proxy in iptables mode. — [vmware-networking-anatomy.md](../vmware-networking-anatomy.md)

## Storage

**Q: What does `WaitForFirstConsumer` do?**
A: Delays volume provisioning until a pod is scheduled, so the volume is created where the pod runs (node for local-path, AZ for EBS). — [vmware-storage-statefulset.md](../vmware-storage-statefulset.md)

**Q: local-path vs EBS?**
A: local-path is node-local (PV pinned to `k8s-worker-02`). EBS is AZ-scoped network storage that can move between nodes in the same AZ. — [adr/013-local-path-vs-ebs-storage.md](../adr/013-local-path-vs-ebs-storage.md)

**Q: What dominated the ~6.3 min EBS recovery after a worker was terminated?**
A: Waiting for the old attachment to detach (`FailedAttachVolume` repeated). Attach → Ready was only ~11–15 s. — [aws-storage-resilience.md](../aws-storage-resilience.md)

**Q: What happened when all `ap-south-1b` nodes were cordoned?**
A: The pod stayed Pending: "0/3 nodes are available: 1 Too many pods, 2 node(s) were unschedulable". The expected "volume node affinity conflict" never appeared because the only other-AZ node was full, so the AZ constraint was only partly demonstrated. — [aws-storage-resilience.md](../aws-storage-resilience.md)

**Q: Does persistent storage mean you have a backup?**
A: No. EBS persistence survives pod and node loss, but not volume deletion or an AZ outage without a snapshot. — [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md)

## Security

**Q: Does a ServiceAccount have permissions by itself?**
A: No. A Role or ClusterRole grants nothing until a RoleBinding or ClusterRoleBinding binds it. — [security-rbac.md](../security-rbac.md)

**Q: RoleBinding referencing a ClusterRole: what scope?**
A: Only the RoleBinding's namespace. `security-pod-viewer` through a RoleBinding only worked inside `security-lab`. — [security-rbac.md](../security-rbac.md)

**Q: What PSA levels were set on `security-lab`?**
A: enforce `baseline`, audit/warn `restricted`. A root-user pod was admitted under baseline with restricted warnings. — [security-rbac.md](../security-rbac.md)

**Q: How was the app's ServiceAccount hardened?**
A: A dedicated ServiceAccount with `automountServiceAccountToken: false`, non-root UID 10001. — [security-rbac.md](../security-rbac.md)

**Q: First step when a user gets Forbidden?**
A: `kubectl auth can-i ... --as=...` and inspect bindings. Diagnose before you grant anything; never reach for cluster-admin. — [runbooks/rbac-access-denied.md](../runbooks/rbac-access-denied.md)

## Automation

**Q: Python vs Ansible vs Terraform vs Argo in Project 1?**
A: Terraform: AWS infrastructure lifecycle. Argo: Kubernetes desired state. Python (`platform-automate`): custom API logic, checks, reports. Ansible: host and service configuration. — [adr/010-python-and-ansible-automation-boundary.md](../adr/010-python-and-ansible-automation-boundary.md)

**Q: What stops the Python CLI from causing damage?**
A: `--dry-run` / `--confirm` guards, `ops` commands are read-only, only `automation-lab` may be mutated, Terraform is plan-only, and `shell=True` is never used. — [automation/platform-automation-master-guide.md](../automation/platform-automation-master-guide.md)

**Q: What does idempotency look like in Ansible here?**
A: A second run of the same playbook reports `changed=0` (playbook `06_idempotency`). — [../../automation/ansible/README.md](../../automation/ansible/README.md)

**Q: Why was Ansible run from Linux/Jenkins and not the Windows workstation?**
A: `ansible-runner` / the Ansible CLI is blocked on Windows (`fcntl`); the Python package falls back to subprocess. — [../../automation/python/README.md](../../automation/python/README.md)

**Q: Why not write automation that re-applies manifests?**
A: It would become a second reconciler fighting Argo CD. Automation checks and reports; Git + Argo change state. — [automation/platform-automation-master-guide.md](../automation/platform-automation-master-guide.md)

## DR

**Q: HA vs backup vs DR?**
A: HA keeps serving through a component failure. A backup is a copy. DR means rebuilding and verifying service within an RTO/RPO; just having a backup is not DR. — [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md)

**Q: What did the EBS snapshot drill measure?**
A: Snapshot ReadyToUse ~72 s; restore PVC → Running ~15 s; restored volume had POINT-A but not POINT-B (RPO window ≈74 s). — [dr-lab-evidence.md](../dr-lab-evidence.md)

**Q: Why did the first snapshot restore fail?**
A: A PVC `dataSource` VolumeSnapshot must be in the same namespace. Fix: static VolumeSnapshotContent + VolumeSnapshot in `dr-storage-restore`. — [postmortems/cross-namespace-snapshot-restore.md](../postmortems/cross-namespace-snapshot-restore.md)

**Q: What did namespace deletion recovery prove?**
A: Declarative objects came back from Git in ≈23 s. Runtime memory, ephemeral data and anything not in Git did not. — [dr-lab-evidence.md](../dr-lab-evidence.md)

**Q: What DR was NOT tested?**
A: AWS Backup for EKS restore, full EKS rebuild, cross-region DR, full AZ loss. — [portfolio/known-limitations.md](./known-limitations.md)

## Operations

**Q: First principle of every runbook?**
A: Read-only evidence first, then plan, confirm, execute, verify ("evidence before mutation"). — [operations/platform-operations-handbook.md](../operations/platform-operations-handbook.md)

**Q: Which postmortems exist?**
A: Grafana OOM, VMware ingress SPOF, failed rollout 0.1.5, VMware worker failure, Argo ComparisonError, cross-namespace snapshot restore. — [operations/README.md](../operations/README.md)

**Q: Why record "Observed vs untested"?**
A: So nobody claims tested behaviour that was only designed. — [operations/observed-vs-untested.md](../operations/observed-vs-untested.md)

**Q: What did the VMware cleanup keep?**
A: Control plane, 3 nodes, Calico, CoreDNS, kube-proxy, Metrics Server, local-path. Everything Project 1 added was removed. — [operations/vmware-lab-cleanup.md](../operations/vmware-lab-cleanup.md)

**Q: What is the Git rollback decision rule?**
A: Prefer reverting or re-pinning in Git and letting Argo reconcile over imperative `kubectl` changes that selfHeal will undo. — [runbooks/git-rollback.md](../runbooks/git-rollback.md)
