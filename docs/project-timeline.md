# Project timeline

```text
Foundation → CI/CD → GitOps → AWS → Observability → Reliability
→ Security → Automation → DR → Operations → Portfolio
```

| Phase | Highlights | Example commits |
|---|---|---|
| Foundation | VMware kubeadm platform | early platform commits |
| CI/CD | Jenkins publish | `91b5800`, `0a633da` |
| GitOps | Argo local + multi-env | `71ed15b`, `baec457` |
| AWS | Terraform EKS | `5e304cd` |
| Observability | Prom/Grafana both envs | `1c562fc`, `a37bc92` |
| Reliability | HPA/PDB/failures | `bc8181f`, `302a506` |
| Networking HA | MetalLB, ingress HA | `bfeb721`, `eb622e9` |
| Storage | local-path, EBS, resilience | `f33876d`, `c8d45ca` |
| Security | RBAC/PSA | `85d76a6` |
| Advanced Argo | AppSet, waves | `6d57e42` |
| Automation | Python/Ansible | `5593a26` |
| DR | Snapshots, RPO/RTO | `2a013bd` |
| Operations | Handbook/runbooks | `8e09fd7` |
| Portfolio | Section 27 | final commit |

Not every commit listed — see [commit-map.md](portfolio/commit-map.md).
