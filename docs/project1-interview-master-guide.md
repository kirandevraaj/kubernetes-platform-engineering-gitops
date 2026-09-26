# Project 1 Interview Master Guide

**Repo:** https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops  
**App:** `0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

Companion deep dives: [argo-cd-interview-notes.md](./argo-cd-interview-notes.md) · [operations/operations-interview-notes.md](./operations/operations-interview-notes.md) · [automation-interview-notes.md](./automation-interview-notes.md) · [disaster-recovery-interview-notes.md](./disaster-recovery-interview-notes.md) · [portfolio/project1-interview-cheat-sheet.md](./portfolio/project1-interview-cheat-sheet.md)

---

## 60-second pitch

This is a **portfolio Kubernetes platform engineering lab**, not a production customer platform. I built a dual-environment system on **VMware kubeadm** and **AWS EKS** with **Terraform** for AWS infrastructure, **Jenkins** for CI and digest promotion, and **Argo CD** for GitOps reconciliation. The same immutable image digest runs in both environments. I added **Prometheus/Grafana** observability, **RBAC/Pod Security**, **HPA/PDB**, MetalLB/ingress HA on VMware and ALB on AWS, **EBS CSI** persistence with snapshot restore drills, **Python/Ansible** automation, and **operational runbooks**. I ran controlled failure experiments—bad rollouts, node loss, ingress SPOF, Argo ComparisonError—and measured lab recovery timings. Limitations are explicit: no multi-region DR, AWS Backup restore not executed, AWS NetworkPolicy enforcement not observed, and AWS observability can report Degraded under pod-density surge while Grafana still serves.

## 5-minute walkthrough

1. Architecture SVG · 2. Jenkins→digest→Git · 3. Argo Synced · 4. EKS Terraform · 5. Observability · 6. Security-lab · 7. Failure postmortems · 8. Storage/EBS · 9. DR timings · 10. Automation CLI + limitations

---

## Domain notes (What / Why / How / Tested / Learned / Limits)

### Architecture
Built dual-env platform to mirror real split of on-prem vs cloud. Control plane ≠ data plane. Limit: lab scale (2–3 workers).

### Kubernetes
Deployments, Services, probes, HPA, PDB, topology, events. Tested pod delete, NotReady, Pending (density). Learned Running≠Ready≠Serving.

### Terraform / AWS
VPC/EKS/IAM/add-ons. Tested apply path; **not** destructive full rebuild. Single NAT cost tradeoff. Local state gap.

### Jenkins / Git
CI gated on app changes; promote digests; GitOps-only skips. Learned loop prevention.

### Argo CD
Separate CPs; AppProject restrictions; AppSets; waves; ComparisonError from kustomize. selfHeal ~6s. Prefer Git rollback.

### Observability
Prom/Grafana/KSM/node-exporter/Metrics Server distinct roles. AWS Degraded freeze note.

### Networking
MetalLB+ingress vs ALB IP. Ingress HA after SPOF. AWS NP partial.

### Storage
local-path vs EBS AZ. Snapshot Ready ~72s; restore ~15s; cross-ns failure lesson.

### Security
Least privilege SA, PSA baseline, RBAC can-i. No prod secret manager.

### Python / Ansible
`platform-automate` doctor/verify/ops_*; Ansible Linux-only here.

### DR / Operations
Measured drills; runbooks; handbook; evidence redaction. AWS Backup assessed only.

---

## Deep-dive questions (answer from Project 1)

### Kubernetes (sample of 15 themes)
Pending causes? NotReady vs CrashLoop? Endpoints empty? HPA needs? PDB vs HPA? Topology spread? Resource requests? Events first? Rollout surge stuck? Node NotReady taints? StatefulSet vs Deploy? PVC Pending? ImagePullBackOff? Service selector mismatch? kubectl top vs Prometheus?

### Argo (15 themes)
Synced vs Healthy? OutOfSync? ComparisonError? selfHeal? AppProject deny? ApplicationSet owner? Hook failure? Wave dependency? Manual app delete? Multi-source? IgnoreDifferences? Refresh vs sync? Separate CPs why? Progressing forever? Git as SoT?

### Terraform/AWS (15 themes)
Plan before apply? State risks? EKS shared responsibility? Node group replace? NAT single AZ? ALB target IP? EBS AZ? Security groups? IAM vs RBAC? Add-ons? Drift? Destroy not normal? Public IP cost? Pod Identity? Subnet tags for LBC?

### Observability (10)
Metrics Server≠Prometheus? KSM purpose? Target DOWN triage? /metrics path? Grafana OOM? Control-plane scrape noise? HPA metric source? Dashboard as code? Cardinality? Alerting gap?

### Networking (10)
MetalLB L2? VIP fail? Ingress SPOF? ALB unhealthy? Service no endpoints? NP VMware vs AWS? Host header? CoreDNS? Cross-node? PDB for ingress?

### Storage (10)
CSI role? Pending PVC? FailedAttachVolume? AZ bind? Snapshot classes? Cross-ns restore? local-path limits? RWO? VolumeAttachment? Restore verification?

### Security (10)
can-i flow? SA automount? PSA modes? Privileged deny? Secret hygiene? AppProject destination deny? IAM confusion? NetPolicy false sense on AWS? cluster-admin anti-pattern? Incident evidence?

### Python/Ansible (15)
doctor first? ops read-only? redact fail-closed? Boto3 vs TF? Ansible check/diff? FQCN? Vault? Idempotency? Runner? Windows block? Exit codes? Structured reports? Parallelism? Inventory? When not to automate?

### DR (10)
RTO measure? RPO? What Git restores? What snapshots restore? AWS Backup status? Why not claim multi-region? Namespace drill? selfHeal? People/creds deps? Evidence timeline?

### Operations (10)
First 60s? SEV model? Escalate when? Evidence fields? Anti-patterns? Git rollback tree? Daily health? Postmortem blameless? Stabilization first? Why not hide Degraded?

*(Use companion interview notes for extended Q&A text.)*
