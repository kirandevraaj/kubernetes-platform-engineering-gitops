# Evidence index

Portfolio evidence map. No secret-bearing artifacts.

| Category | Evidence | Documentation | Commit (examples) | Environment |
|---|---|---|---|---|
| CI/CD | Jenkins promote 0.1.x | Jenkinsfile, release notes | `0a633da`, `0590eb7` | Both overlays |
| GitOps | Argo Synced/Healthy | argo docs | `71ed15b`, `baec457` | Both |
| Digest | 0.1.4 pin | overlays | `5da676f` | Both |
| Observability | Stacks running | observability docs | `1c562fc`, `a37bc92` | Both |
| Reliability | HPA/PDB labs | reliability docs | `bc8181f` | Both |
| Failure | Rollout/selfHeal/pod | postmortems | `302a506`, `95820c8` | VMware |
| Networking | MetalLB/ingress HA | networking docs | `bfeb721`, `eb622e9` | VMware |
| Storage | PVC Bound / EBS | storage docs | `f33876d`, `bd5e6dc`, `c8d45ca` | Both |
| Security | security-lab | security-rbac | `85d76a6` | Both |
| Automation | platform-automate | automation guide | `5593a26` | Workstation |
| DR | Measured timings | dr-lab-evidence | `2a013bd` | AWS+GitOps |
| Operations | Handbook/runbooks | operations/ | `8e09fd7` | Docs |

See [commit-map.md](../portfolio/commit-map.md).
