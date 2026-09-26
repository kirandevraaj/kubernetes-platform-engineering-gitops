# Daily platform health checklist

**Cadence:** Daily (or start of shift)  
**Scope:** VMware `ckad-lab` and AWS `platform-lab-aws` — run both if you operate both.  
**Rule:** All commands below are **READ-ONLY** unless noted.

Related: [operator-shift-checklist.md](./operator-shift-checklist.md) · [golden-signals.md](../operations/golden-signals.md)

---

## 1. Context

| # | Check | Command (READ-ONLY) | Pass criteria |
|---|---|---|---|
| 1.1 | VMware context | `kubectl config use-context ckad-lab` | Context name correct |
| 1.2 | AWS context | `kubectl config use-context platform-lab-aws` (tools container) | Context name correct |

---

## 2. Nodes

| # | Check | Command | Pass |
|---|---|---|---|
| 2.1 | Node Ready | `kubectl get nodes` | 3 Ready (VMware); 2 Ready (AWS t3.medium) |
| 2.2 | Node conditions | `kubectl describe node` (if NotReady) | No unexpected pressure |

---

## 3. Core workloads — `platform-lab`

| # | Check | Command | Pass |
|---|---|---|---|
| 3.1 | Deployment | `kubectl get deploy -n platform-lab` | 2/2 available |
| 3.2 | Pods | `kubectl get pods -n platform-lab -o wide` | Running, Ready |
| 3.3 | Image digest | `kubectl get deploy -n platform-lab -o jsonpath='{.spec.template.spec.containers[0].image}'` | Tag `0.1.4`; digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` when pinned |

---

## 4. Argo CD

| # | Check | Command | Pass |
|---|---|---|---|
| 4.1 | Applications | `kubectl get applications -n argocd` | Production apps Synced/Healthy |
| 4.2 | Degraded / Unknown | filter above | None for platform-lab, storage, security |

---

## 5. HPA

| # | Check | Command | Pass |
|---|---|---|---|
| 5.1 | HPA status | `kubectl get hpa -n platform-lab` | Desired replicas sane at idle |

---

## 6. Storage

| # | Check | Command | Pass |
|---|---|---|---|
| 6.1 | PVCs | `kubectl get pvc -A \| findstr /V Bound` (or `grep -v Bound`) | No unexpected Pending |
| 6.2 | storage-lab | `kubectl get sts,pvc -n storage-lab` | Bound; AWS vol `vol-05faa26874d720ecd` in-use (**Observed** baseline) |

---

## 7. Observability

| # | Check | VMware | AWS |
|---|---|---|---|
| 7.1 | Prometheus | Pods Ready in `monitoring` | Pods Ready in `observability` |
| 7.2 | Grafana | Service/LB reachable | Per overlay |
| 7.3 | Scrape health | Spot-check `/metrics` target for app | Same |

---

## 8. Ingress / load balancing

| # | Environment | Check | Pass |
|---|---|---|---|
| 8.1 | VMware | ingress-nginx 2/2; VIP `192.168.56.200` | `/health` 200 via Host header |
| 8.2 | AWS | ALB ingress | Target healthy; `/health` 200 |

---

## 9. Recent change awareness

| # | Check | Source |
|---|---|---|
| 9.1 | Git commits | `git log -3 --oneline` |
| 9.2 | Argo revision | Application status |
| 9.3 | Failed Jenkins builds | Jenkins UI (READ-ONLY) |

---

## 10. Errors / events (sample)

| # | Command | Pass |
|---|---|---|
| 10.1 | `kubectl get events -A --field-selector type=Warning --sort-by='.lastTimestamp'` | Review; no storm on platform-lab |

---

**Not tested in Project 1:** Automated daily execution of this checklist via cron — **Design guidance** only.
