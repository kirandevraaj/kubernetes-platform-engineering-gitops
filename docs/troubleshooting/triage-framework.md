# Operator triage framework (Project 1 — Section 26)

**Purpose:** Answer at 2 AM: *what layer is broken, how bad is it, what is safe to do first?*  
**Principle:** OBSERVE → UNDERSTAND → ACT → VERIFY → LEARN ([platform-operations-handbook.md](../operations/platform-operations-handbook.md)).

Cross-links: [troubleshooting-matrix.md](./troubleshooting-matrix.md) · [golden-signals.md](../operations/golden-signals.md) · [incident-response-playbook.md](../operations/incident-response-playbook.md)

---

## STEP 1 — Classify the failure domain

Ask: is the issue **application**, **Kubernetes workload**, **node**, **network**, **storage**, **GitOps (Git/Jenkins/Argo)**, **AWS control plane/data plane**, or **external** (DNS, registry, GitHub)?

| Layer | Typical symptoms | Project 1 pointer |
|---|---|---|
| Application | Wrong version, app logs, `/health` body | `platform-lab` 0.1.4 digest pin |
| Kubernetes | Pending/CrashLoop/NotReady, Deployment not Available | Pod delete ~10–14s recovery (**Observed**) |
| Node | Node NotReady, reduced capacity | VMware kubelet stop; AWS worker terminate (~6.3 min EBS path) |
| Network | 502/503, no endpoints, policy deny | Ingress VIP `192.168.56.200`; AWS ALB; NetworkPolicy differs by env |
| Storage | PVC Pending, mount failures | `local-path` vs `ebs-gp3`; vol `vol-05faa26874d720ecd` |
| GitOps | OutOfSync, ComparisonError, Degraded Application | [argo-advanced-patterns.md](../argo-advanced-patterns.md) |
| AWS | API errors, EBS AZ, ALB target unhealthy | [aws-storage-resilience.md](../aws-storage-resilience.md) |
| External | Cannot clone Git, cannot pull image | **Design guidance** unless explicitly tested |

**READ-ONLY — confirm context**

| Class | Command |
|---|---|
| READ-ONLY | `kubectl config current-context` |
| READ-ONLY | `kubectl get nodes` |
| READ-ONLY | `kubectl get application -n argocd` |

---

## STEP 2 — Determine blast radius

| Question | Why |
|---|---|
| One namespace or many? | Isolation vs platform-wide |
| One cluster or both? | VMware and AWS are **separate** Argo control planes |
| Read path vs write path? | Ingress/ALB vs batch jobs |
| Stateful data at risk? | PVC/EBS vs stateless Deployment |

**Observed in Project 1:** Failed 0.1.5 rollout kept old ReplicaSet serving traffic while new RS failed readiness — degraded rollout, not full outage ([failed-rollout runbook](../runbooks/failed-rollout.md) when present).

---

## STEP 3 — Service health state

| State | Meaning | Operator focus |
|---|---|---|
| **Healthy** | SLO-ish signals green; investigate noise/alerts |
| **Degraded** | Partial capacity, elevated errors, single replica down |
| **Unavailable** | User-visible failure or zero ready endpoints |

Map to golden signals: [golden-signals.md](../operations/golden-signals.md).

---

## STEP 4 — Recent changes

Check in order (READ-ONLY):

| Source | Command / location | Class |
|---|---|---|
| Git | `git log -5 --oneline` (repo); Argo `status.sync.revision` | READ-ONLY |
| Argo | `kubectl get application -n argocd -o wide` | READ-ONLY |
| Jenkins | Last build for app pipeline | READ-ONLY |
| Terraform | Last plan/apply note; **do not apply during triage** | READ-ONLY |
| Live drift | Argo OutOfSync; selfHeal ~6s on VMware (**Observed**) | READ-ONLY |

---

## STEP 5 — Collect evidence before changing anything

Minimum bundle: [incident-evidence.md](../operations/incident-evidence.md).  
Timeline template: [incident-timeline-template.md](../operations/incident-timeline-template.md).

**Never capture:** Secret values, tokens, kubeconfig contents, private keys.

---

## STEP 6 — Smallest safe remediation

| Priority | Action type |
|---|---|
| 1 | READ-ONLY diagnosis completion |
| 2 | Restore **desired state** via Git (revert) if bad deploy |
| 3 | SAFE MUTATION with named target (uncordon, scale within Git, Argo sync if policy allows) |
| 4 | DESTRUCTIVE only with explicit approval and runbook WARNING |

GitOps rollback model: Git change → Argo reconcile — **not** `kubectl rollout undo` as default for `platform-lab`.

---

## STEP 7 — Verify

| Check | VMware | AWS |
|---|---|---|
| App | `curl -H "Host: platform-lab.local" http://192.168.56.200/health` | ALB `/health` 200 |
| Workload | Deployment 2/2, digest pinned | Same digest |
| GitOps | Application Synced/Healthy | Same |
| Storage | PVC Bound | PVC Bound; EBS in-use |
| Observability | Prometheus targets, Grafana | observability namespace |

Document T0→recovery in timeline; compare to [rpo-rto-operational-guide.md](../operations/rpo-rto-operational-guide.md) (**lab observations, not SLA**).

---

## Quick reference diagram

See [platform-failure-domain.svg](../diagrams/platform-failure-domain.svg) when present — user path (DNS/ALB/MetalLB → ingress → Service → Pod) vs control path (Git → Jenkins → Argo → API).
