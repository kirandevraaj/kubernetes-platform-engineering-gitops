# GitOps flow

Status: planned. No Argo CD Application, AppProject, or ApplicationSet exists yet.

## Intended flow

1. Git is the source of truth for Kubernetes desired state.
2. An Argo CD Project limits which repositories and namespaces a team of applications may use.
3. An Application points at `kubernetes/overlays/local` or `kubernetes/overlays/aws`.
4. Argo CD renders the overlay and converges the matching cluster.
5. Drift is corrected from Git. A manual cluster edit is temporary until the same change is committed.

## Repository map

| Path | Future contents |
|---|---|
| `kubernetes/base` | Shared workload manifests |
| `kubernetes/overlays/local` | Local lab patches |
| `kubernetes/overlays/aws` | AWS patches |
| `gitops/projects` | AppProject definitions |
| `gitops/applications` | Application definitions |
| `gitops/appsets` | ApplicationSet definitions, if one pattern must cover both targets |

Local and AWS Applications stay as separate objects so a sync of one cannot select the other cluster.
