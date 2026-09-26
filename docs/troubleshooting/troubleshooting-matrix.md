# Troubleshooting matrix (Phase 60 — Project 1)

**Legend:** Command class — **R** = READ-ONLY, **S** = SAFE MUTATION, **D** = DESTRUCTIVE (avoid during first pass).

| Symptom | Likely layer | First check | Second check | Useful command (class) | Safe action | Escalation |
|---|---|---|---|---|---|---|
| HTTP 5xx | Ingress / app / endpoints | Context + ingress/ALB health | Deployment ready replicas, EndpointSlice | `kubectl get deploy,po -n platform-lab` (R); VMware: curl VIP `/health` (R) | READ-ONLY triage; Git rollback if bad release | SEV-1 if all paths 5xx; [escalation.md](../operations/escalation.md) |
| Pods Pending | Scheduling / storage / resources | Events on Pod | PVC, node capacity, topology | `kubectl describe pod <name> -n <ns>` (R) | Fix root cause in Git (requests, SC, affinity); **not** random delete | Pending >15m or critical workload |
| Pod CrashLoopBackOff | App / config / image | `kubectl logs --previous` (R) | Image pull, probes, ConfigMap | `kubectl describe pod` (R) | Git fix + Argo sync; rollback bad image tag/digest | Data loss risk or widespread crash |
| Pod NotReady | Readiness probe / deps | Probe config in Git | Service endpoints count | `kubectl get endpointslices -n platform-lab` (R) | Fix readiness in Git; **Observed:** RS may not replace NotReady alone | User-facing if endpoints=0 |
| Deployment Progressing | Rollout stuck | ReplicaSet generations | New RS not Ready | `kubectl get rs -n platform-lab` (R) | Git rollback to 0.1.4 digest (**Observed** 0.1.5 case) | Old RS also failing |
| Argo OutOfSync | GitOps drift / manual edit | App sync status, diff | selfHeal, sync policy | `kubectl get application -n argocd <app> -o yaml` (R) | Revert live drift via Git; optional sync after review (S) | Cannot sync + production impact |
| Argo ComparisonError | Manifest generation | Application conditions message | Kustomize paths, repo structure | `kubectl describe application` (R) | Fix repo layout (**Observed:** waves-health `../base/namespace.yaml`) | All apps ComparisonError |
| Argo Degraded | Underlying resource unhealthy | Managed resource health | Deployment/Pod state | `argocd app get` / kubectl Application (R) | Fix workload or Git; see [argo-outofsync.md](../runbooks/argo-outofsync.md) | Platform app Degraded |
| No Service endpoints | Readiness / selectors | EndpointSlice addresses | Pod labels vs Service selector | `kubectl get endpointslices -n platform-lab -o wide` (R) | Fix selector/readiness in Git | Zero endpoints on prod Service |
| Ingress unavailable | MetalLB / ingress-nginx | ingress controller pods | VIP assignment | `kubectl get pods -n ingress-nginx` (R); VIP `192.168.56.200` | Restore HA replicas via Git (**Observed** SPOF fix) | VIP unreachable |
| ALB unhealthy | AWS LB / targets / pods | Target group health | Pod readiness, `/health` | AWS console/CLI describe target health (R) | Fix pods/network in cluster; GitOps path | All targets unhealthy |
| PVC Pending | StorageClass / CSI / quota | PVC events | StorageClass, snapshot class | `kubectl describe pvc` (R) | Git fix SC/ size; capacity add (terraform) — planned | Stateful workload blocked |
| EBS attach failure | CSI / AZ / node | VolumeAttachment | PV nodeAffinity, AZ | `kubectl get volumeattachment` (R) | Same-AZ worker (**Observed** [aws-storage-resilience.md](../aws-storage-resilience.md)) | Data volume stuck detached |
| HPA not scaling | metrics-server / requests | `kubectl top` works? | HPA status, CPU metrics | `kubectl describe hpa -n platform-lab` (R) | Fix requests/limits or metrics-server in Git | Autoscaling required for load event |
| Prometheus target down | Scrape config / network | Target status UI | ServiceMonitor, NP, port `/metrics` | Port-forward Prometheus or UI (R) | Fix SM labels/ports in Git | Critical alerts blind |
| Grafana unavailable | Pod / LB / resources | Grafana pod status | Service type, MetalLB pool | `kubectl get pods,svc -n monitoring` (R) | GitOps resource fix (**Observed** OOM history) | No dashboards during incident |
| RBAC denied | Authorization | `kubectl auth can-i` as subject | RoleBinding chain | `kubectl auth can-i --list --as=system:serviceaccount:...` (R) | Git RBAC fix; **do not** grant cluster-admin ad hoc | Security incident if unexpected admin |
| NetworkPolicy blocked | CNI enforcement | CNI type (Calico vs VPC CNI) | Policy selectors/ports | `kubectl get networkpolicy -n platform-lab` (R) | Adjust policy in Git | **Observed:** enforced VMware; **not** enforced AWS lab config — [security-rbac.md](../security-rbac.md) |
| Jenkins failure | CI | Build log stage | Git webhook, agent | Jenkins UI (R) | Fix pipeline; GitOps-only changes skip build (**Observed** pattern) | Cannot publish new digest |
| Docker push failure | Registry / CI | Build log push stage | Auth (no secrets in tickets) | Jenkins log (R) | Retry; fix credentials out-of-band | Release blocked |
| Terraform plan unexpected | IaC drift | `terraform plan` (R) | State vs code | `terraform plan` in `terraform/aws` (R) | **Never** blind apply; review diff | Infra change needed for recovery |

**Related:** [triage-framework.md](./triage-framework.md) · [common-issues.md](./common-issues.md) · [platform-operations-handbook.md](../operations/platform-operations-handbook.md)
