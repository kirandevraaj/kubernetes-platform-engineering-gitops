# Local Kubernetes networking

Status: Ingress and NetworkPolicy for `platform-lab` are defined in Git under `kubernetes/base` and reconciled by Argo CD on `ckad-lab`. This step is HTTP only. TLS is not configured yet.

## Traffic path (local lab)

```text
Windows host
    |
    |  HTTP :30080  (Host: platform-lab.local)
    v
NodePort on any Ready node (ingress-nginx-controller)
    |
    v
ingress-nginx controller pod (namespace ingress-nginx)
    |
    v
Ingress platform-lab (host platform-lab.local, path /)
    |
    v
Service platform-lab :8000 (ClusterIP)
    |
    v
platform-lab Pods :8000
```

NodePorts on this cluster: **30080** (HTTP), **30443** (HTTPS, unused in this step). Reach a worker or control-plane node on the host-only network `192.168.56.0/24` (for example `192.168.56.11` or `192.168.56.12`).

Example:

```powershell
curl.exe -s -H "Host: platform-lab.local" http://192.168.56.11:30080/health
```

Do not use Docker Desktop Kubernetes. Do not use `kubectl port-forward` as the primary ingress proof for this step.

## Ingress

| Field | Value |
|---|---|
| Manifest | `kubernetes/base/ingress.yaml` |
| Name / namespace | `platform-lab` / `platform-lab` |
| IngressClass | `nginx` (existing `ingress-nginx`) |
| Host | `platform-lab.local` |
| Path | `/` Prefix → Service `platform-lab:8000` |
| TLS | None in this step |

No second ingress controller is installed. The Service remains ClusterIP.

## NetworkPolicy

| Field | Value |
|---|---|
| Manifest | `kubernetes/base/networkpolicy.yaml` |
| Scope | Namespace `platform-lab` only |
| Pod selector | `app.kubernetes.io/name=platform-lab`, `app.kubernetes.io/instance=platform-lab` |
| Allowed ingress | Pods in namespace `ingress-nginx` with labels `app.kubernetes.io/name=ingress-nginx` and `app.kubernetes.io/component=controller` |
| Port | TCP 8000 |
| Egress | Not restricted in this first policy |

Namespace matching uses the automatic label `kubernetes.io/metadata.name=ingress-nginx`.

Purpose: only the ingress controller should reach the application pods on the Service port. Unrelated namespaces are not selected.

## Why this lives in GitOps

Networking desired state is part of the workload package. Jenkins does not apply Ingress or NetworkPolicy. A commit under `kubernetes/**` is reconciled by Argo CD Application `platform-lab-local`. That keeps CI (image publish) separate from CD (cluster converge).

## Local versus future AWS

| Concern | Local lab | AWS (later) |
|---|---|---|
| Entry | ingress-nginx NodePort 30080/30443 | Likely a load balancer / different Ingress annotations |
| Host | `platform-lab.local` | Environment-specific hostname |
| Overlay | Same base Ingress/NetworkPolicy today; AWS may patch later | Keep AWS overlay independent until that path exists |
| Image tag | Local overlay `0.1.2` | AWS overlay still base default `0.1.0` |

## AppProject note

Argo CD AppProject `platform-lab` must allow `networking.k8s.io` `Ingress` and `NetworkPolicy`. That ACL lives in `gitops/projects/platform-lab.yaml` and is applied to the `argocd` namespace as Argo CD control-plane configuration (not by the Application sync of `kubernetes/overlays/local`).

## Validation results

Filled after GitOps reconciliation of this step.
