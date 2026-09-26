# Failure engineering stories

| Story | Situation | Observation | Root cause | Action | Lesson |
|---|---|---|---|---|---|
| Grafana OOM | VMware Grafana unstable | OOMKills | Low memory limit | GitOps raise limits | Size observability |
| Ingress SPOF | Worker loss | Ingress down | 1 replica | 2 replicas+PDB | Ingress is platform HA |
| Failed 0.1.5 | Bad release | New RS not Ready; old serves | Bad readiness/image | Git rollback digest | Git>undo |
| Worker VMware | kubelet stop | NotReady | Node failure | Restart kubelet | Node≠pod-only |
| ComparisonError | waves-health Unknown | No manifests | Bad kustomize path | Self-contained kustomization | Source gen errors |
| Snapshot cross-ns | Restore failed | Pending/errors | Namespace/VSC rules | Same-ns static VSC | Check binding early |
| EBS node | Worker terminate | Attach delay | AZ + CSI | Same-AZ worker | ~6.3 min lab |
| RBAC denial | Forbidden | can-i no | Missing bind | Least privilege Git | Diagnose before grant |
| PSA | Warn/deny | Admission | Spec vs baseline | Fix securityContext | PSA labels matter |
| HPA | Load | Scale 2→4 / 2→3 | Metrics+requests | Leave HPA owner | Timing varies |

Details: `docs/postmortems/`
