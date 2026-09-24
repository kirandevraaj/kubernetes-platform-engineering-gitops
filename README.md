# Kubernetes Platform Engineering & GitOps Lab

A portfolio project that builds a small platform around a containerized application: Kubernetes delivery, infrastructure as code, CI, GitOps CD, an AWS deployment path, networking, observability, and Python automation.

## Project objective

Show how a platform engineer takes an application from source to a running Kubernetes workload, with a repeatable local lab and a separate AWS target. Each layer is added only after the previous one is documented and working.

The current lab cluster is an existing three-node environment used as the local runtime. The FastAPI application lives under `app/`, and its container image is published on Docker Hub as `kirandevraaj/platform-lab:0.1.2`. The local overlay is reconciled by Argo CD from Git onto that cluster. Jenkins CI on Docker Desktop polls GitHub, publishes versioned images when `app/**` changes, and commits the local overlay image tag. It does not deploy. Automated promotion of `0.1.2` was demonstrated on 24 September 2026. Terraform resources are not included yet.

## Architecture overview

The diagram below is the intended shape. The Python application is containerized and version `0.1.2` is published and running on the local lab. Jenkins CI publishes that image and promotes the local GitOps overlay. Argo CD reconciles the overlay from Git. Terraform and the AWS target are not implemented. The local VMware lab is the only Kubernetes runtime that exists today.

```text
Developer
   |
   v
Git repository
   |
   +--> container image (published: kirandevraaj/platform-lab:0.1.2)
   |
   +--> Jenkins CI (pollSCM, app/** gated) --> image publish + local GitOps promote
   |
   +--> Argo CD / GitOps (local overlay synced) --> Kubernetes
                                          |
                                          +--> local lab (VMware Workstation, current runtime)
                                          |
                                          +--> AWS target (planned, separate)

Observability: Prometheus, Grafana, OpenTelemetry (planned)
Automation: Python (planned)
Infrastructure: Terraform / AWS path (planned)
```

```mermaid
flowchart LR
  developer[Developer]
  github[GitHub]
  jenkins[Jenkins CI]
  hub[Docker Hub]
  argocd[Argo CD]
  k8s[Kubernetes]
  vmware[local VMware cluster]

  developer --> github
  github --> jenkins
  jenkins --> hub
  github --> argocd
  hub --> k8s
  argocd --> k8s
  k8s --> vmware
```
Local runtime observed on 24 September 2026 (read-only):

| Node | Role | Address | OS | Kubernetes | Runtime |
|---|---|---|---|---|---|
| k8s-ctrl-01 | control-plane | 192.168.56.10 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-01 | worker | 192.168.56.11 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-02 | worker | 192.168.56.12 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |

Platform components already running in the local cluster: Calico v3.30.7 (CNI), CoreDNS, kube-proxy, metrics-server, ingress-nginx (MetalLB LoadBalancer on the local overlay), MetalLB L2 pool `lab-pool`, and the local-path provisioner. The application workload `platform-lab` is deployed in namespace `platform-lab` from `kubernetes/overlays/local`: two replicas of `kirandevraaj/platform-lab:0.1.2` and a ClusterIP Service on port 8000. External HTTP uses Host `platform-lab.local` via the MetalLB VIP. The AWS overlay is not applied.

## Technology stack

Present in the local lab now:

| Area | What is there |
|---|---|
| Local infrastructure | VMware Workstation Pro on Windows 11 |
| Node OS | Ubuntu 24.04.4 LTS |
| Orchestration | Kubernetes v1.31.14 |
| Node runtime | containerd 2.2.1 |
| Networking | Calico v3.30.7, ingress-nginx, MetalLB |
| Application | Python FastAPI service under `app/`, version 0.1.2, running in namespace `platform-lab` on the local cluster |
| Published image | `kirandevraaj/platform-lab:0.1.2` on Docker Hub |

Planned, and not in this repository yet:

| Area | Tool |
|---|---|
| Observability | Prometheus, Grafana, OpenTelemetry |
| AWS path | Terraform |

The Jenkins controller and Linux agent run on Docker Desktop (http://127.0.0.1:8080). Job `platform-lab-ci` uses credential `dockerhub-platform-lab` and publishes `kirandevraaj/platform-lab:<APP_VERSION>`. It does not deploy to Kubernetes.

Docker Desktop client 29.6.1 builds the local image. It is not the cluster runtime. Terraform is not installed.

## Environment strategy

Two deployment targets stay separate for the life of this project.

| Target | Purpose | How it is reached |
|---|---|---|
| Local lab | Day-to-day platform work on the three VMware nodes | SSH and kubectl against `192.168.56.0/24` |
| AWS | A future deployment target, to be defined in Terraform and `kubernetes/overlays/aws` | AWS credentials and a distinct kube context, used only when that phase starts |

When those overlays exist, they will describe the same application shape with different infrastructure. A change for one target stays in that target. See [environment strategy](docs/design/environment-strategy.md).

## Implementation status

1. **Repository baseline.** Completed. Project layout, architecture notes, and a read-only record of the current lab.
2. **Application and container image.** Completed. The service, tests, and Dockerfile are in `app/`. Current published tag is `kirandevraaj/platform-lab:0.1.2`. The tag `latest` is not used.
3. **Kubernetes packaging.** Completed. Initially applied on 24 September 2026 with `kubectl apply -k kubernetes/overlays/local`. Ongoing changes are GitOps-only through Argo CD. The AWS overlay has not been applied.
4. **Jenkins CI pipeline definition.** Completed. `jenkins/Jenkinsfile` checks out the repository, tests `app/tests`, reads `APP_VERSION`, builds and validates `kirandevraaj/platform-lab:<APP_VERSION>`, and pushes that tag. See [jenkins/README.md](jenkins/README.md).
5. **Jenkins execution and publishing.** Completed. Job `platform-lab-ci` publishes versioned tags with credential `dockerhub-platform-lab`. Image validation reaches the temporary container over the agent Docker network. No `latest` tag. No Kubernetes deploy from CI.
6. **Argo CD GitOps.** Completed. Argo CD `v3.5.3` is installed in namespace `argocd` on `ckad-lab`. Application `platform-lab-local` watches `kubernetes/overlays/local` on `main` and syncs to namespace `platform-lab` on the in-cluster API. Automated sync, prune, and selfHeal are enabled. See [gitops/README.md](gitops/README.md) and [docs/architecture/gitops-flow.md](docs/architecture/gitops-flow.md).
7. **Manual CI/CD integration test (0.1.1).** Completed on 24 September 2026. Release `0.1.1` was pushed to GitHub; Jenkins built and published `kirandevraaj/platform-lab:0.1.1`; the local overlay was updated to that tag and pushed; Argo CD reconciled without `kubectl apply`; both pods ran `0.1.1`; `GET /` returned version `0.1.1`, environment `local-gitops`, and release `ci-cd-integration-test`. See [docs/architecture/ci-cd-flow.md](docs/architecture/ci-cd-flow.md).
8. **Automated CI/CD promotion.** Completed and demonstrated. `jenkins/Jenkinsfile` uses `pollSCM`, runs build/push/promotion only for `app/**` changes, refuses reused Docker Hub tags, updates only `kubernetes/overlays/local/kustomization.yaml`, and pushes with `github-platform-lab`. Release `0.1.2` was published by Jenkins build `#5` and reconciled by Argo CD without `kubectl apply`. The follow-up promotion commit build `#6` skipped CI/CD stages (loop prevention). See [jenkins/README.md](jenkins/README.md) and [docs/architecture/ci-cd-flow.md](docs/architecture/ci-cd-flow.md).
9. **Networking.** Completed for the local lab. Ingress + NetworkPolicy in `kubernetes/base`; local overlay patches `ingress-nginx-controller` to MetalLB **LoadBalancer** (L2). Application Service stays ClusterIP. See [docs/architecture/networking.md](docs/architecture/networking.md).
10. **Observability.** Planned. Prometheus, Grafana, and OpenTelemetry for the application.
11. **AWS path.** Planned. Terraform for the AWS runtime, kept apart from the VMware lab.
12. **Python automation.** Planned. Repeatable checks and operational helpers.

## Published container artifact

Version `0.1.2` is the current published image used by the local lab. The tag `latest` is intentionally unused. The digest is the immutable reference for that artifact.

| Field | Value |
|---|---|
| Image | `kirandevraaj/platform-lab:0.1.2` |
| Docker Hub | https://hub.docker.com/r/kirandevraaj/platform-lab |
| Digest | `sha256:082e161b0c90d588fe4f045d80a54297881e188a0e6417e71aaa814a66b92c8a` |

```text
docker pull kirandevraaj/platform-lab:0.1.2
docker pull kirandevraaj/platform-lab@sha256:082e161b0c90d588fe4f045d80a54297881e188a0e6417e71aaa814a66b92c8a
```
## Safety note

The local VMware lab and the AWS account are separate deployment targets. Commands, kube contexts, Terraform workspaces, and GitOps applications for one target must not be aimed at the other. Cluster, VM, and network changes wait for explicit approval.

## Layout

```text
kubernetes-platform-engineering-gitops/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── architecture/
│   ├── design/
│   └── troubleshooting/
├── app/
│   ├── src/
│   └── tests/
├── kubernetes/
│   ├── base/
│   └── overlays/
│       ├── local/
│       └── aws/
├── gitops/
│   ├── applications/
│   ├── projects/
│   └── appsets/
├── jenkins/
│   ├── Jenkinsfile
│   ├── README.md
│   └── runtime/
│       ├── compose.yaml
│       ├── controller/
│       └── agent/
├── terraform/
│   └── aws/
└── scripts/
```

## License

MIT. See [LICENSE](LICENSE).
