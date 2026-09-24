# GitOps (Argo CD)

Status: Argo CD runs in the VMware `ckad-lab` cluster and reconciles `platform-lab` from Git. Jenkins does not deploy.

## CI versus CD

| Layer | Owner | Responsibility |
|---|---|---|
| CI | Jenkins on Docker Desktop | Checkout, unit test, build, validate, push `kirandevraaj/platform-lab:<APP_VERSION>` to Docker Hub |
| CD | Argo CD on `ckad-lab` | Read Git, render `kubernetes/overlays/local`, sync the live workload |

Jenkins never runs `kubectl apply`. Argo CD never builds images.

## Source of truth

GitHub repository `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git`, branch `main`, is the desired state for the local overlay. Argo CD compares the live cluster to that path and converges.

## Layout

| Path | Contents |
|---|---|
| `gitops/projects/` | AppProject definitions (allowed repos, destinations, resource kinds) |
| `gitops/applications/` | Application definitions |
| `gitops/appsets/` | Reserved for ApplicationSets when a multi-target pattern is introduced |

Workload manifests stay under `kubernetes/`. GitOps objects only describe how Argo CD watches those manifests.

## Local Application

| Field | Value |
|---|---|
| Manifest | `gitops/applications/platform-lab-local.yaml` |
| Project | `platform-lab` (`gitops/projects/platform-lab.yaml`) |
| Repository | `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git` |
| Revision | `main` |
| Path | `kubernetes/overlays/local` |
| Destination server | `https://kubernetes.default.svc` (in-cluster API of the VMware lab) |
| Destination namespace | `platform-lab` |
| Sync | automated, `prune: true`, `selfHeal: true` |
| Sync options | `CreateNamespace=true`, `ApplyOutOfSyncOnly=true` |

The destination server is the in-cluster Kubernetes API of the same cluster that hosts Argo CD (`ckad-lab` → `https://192.168.56.10:6443`). The Application does not reference `docker-desktop` and does not target AWS.

## Sync policy choices

Automated sync with prune and self-heal is intentional for this personal lab:

- **Automated sync** keeps the live objects aligned with `main` without a manual click after each Git change.
- **selfHeal** restores Git state when someone edits the cluster directly, which is how drift detection is demonstrated.
- **prune** removes objects that Git no longer declares under the Application path, so the overlay stays authoritative.

The AppProject limits sources to this repository and destinations to namespaces `platform-lab` and `ingress-nginx` on the in-cluster server. Allowed kinds include ConfigMap, Service, Deployment, Ingress, and NetworkPolicy. The `ingress-nginx` destination exists so the local overlay can patch the existing controller Service to MetalLB LoadBalancer without managing the full ingress-nginx Helm release.

## Install note

Argo CD was installed into namespace `argocd` on context `ckad-lab` from the pinned upstream manifest `https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml`. Client-side `kubectl apply` failed on the ApplicationSet CRD annotation size limit; `--server-side` completed the install. Docker Desktop Kubernetes was not used.

## Apply the GitOps objects

After Argo CD is Ready:

```powershell
kubectl config current-context   # must be ckad-lab
kubectl --context=ckad-lab apply -f gitops/projects/platform-lab.yaml
kubectl --context=ckad-lab apply -f gitops/applications/platform-lab-local.yaml
kubectl --context=ckad-lab get application -n argocd platform-lab-local
```

## Validation

```powershell
kubectl --context=ckad-lab get application -n argocd platform-lab-local -o jsonpath="{.status.sync.status} {.status.health.status} {.status.sync.revision}{'\n'}"
kubectl --context=ckad-lab get deploy,svc,pods -n platform-lab
kubectl --context=ckad-lab get configmap -n platform-lab platform-lab-config -o jsonpath="{.data.APP_ENVIRONMENT}{'\n'}"
```

## Observed demos

On 24 September 2026:

1. A Git commit changed `APP_ENVIRONMENT` to `local-gitops`. Argo CD synced revision `e2b7964` and the live ConfigMap matched Git.
2. A live patch set `APP_ENVIRONMENT=manual-drift`. Argo CD went OutOfSync, self-healed back to `local-gitops`, and stayed Healthy with Deployment 2/2.