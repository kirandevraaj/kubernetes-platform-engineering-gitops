# Kubernetes Platform Engineering & GitOps Lab

A portfolio project that builds a small platform around a containerized application: Kubernetes delivery, infrastructure as code, CI, GitOps CD, an AWS deployment path, networking, observability, and Python automation.

## Project objective

Show how a platform engineer takes an application from source to a running Kubernetes workload, with a repeatable local lab and a separate AWS target. Each layer is added only after the previous one is documented and working.

The current lab cluster is an existing three-node environment used as the local runtime. The sample application lives under `app/`. Kubernetes manifests, Terraform resources, Jenkins pipelines, and Argo CD resources are not included yet.

## Architecture overview

The diagram below is the intended shape. The Python application exists under `app/` and can be built locally as `kirandevraaj/platform-lab:0.1.0`. That image has not been pushed. Jenkins, Argo CD, Terraform, and the AWS target are not implemented. The local VMware lab is the only Kubernetes runtime that exists today.

```text
Developer
   |
   v
Git repository
   |
   +--> Jenkins CI --------> container image
   |
   +--> Argo CD (GitOps) --> Kubernetes
                                |
                                +--> local lab (VMware Workstation)
                                |
                                +--> AWS target (separate)

Observability: Prometheus, Grafana, OpenTelemetry
Automation: Python
Infrastructure: Terraform (AWS path)
```

Local runtime observed on 24 September 2026 (read-only):

| Node | Role | Address | OS | Kubernetes | Runtime |
|---|---|---|---|---|---|
| k8s-ctrl-01 | control-plane | 192.168.56.10 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-01 | worker | 192.168.56.11 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-02 | worker | 192.168.56.12 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |

Platform components already running in the local cluster: Calico v3.30.7 (CNI), CoreDNS, kube-proxy, metrics-server, ingress-nginx (NodePort 30080/30443), MetalLB, and the local-path provisioner. Application workloads are not deployed yet.

## Technology stack

Present in the local lab now:

| Area | What is there |
|---|---|
| Local infrastructure | VMware Workstation Pro on Windows 11 |
| Node OS | Ubuntu 24.04.4 LTS |
| Orchestration | Kubernetes v1.31.14 |
| Node runtime | containerd 2.2.1 |
| Networking | Calico v3.30.7, ingress-nginx, MetalLB |
| Application | Python FastAPI service under `app/`, version 0.1.0, not yet deployed |
| Local image | `kirandevraaj/platform-lab:0.1.0`, built on the workstation and not pushed |

Planned, and not in this repository yet:

| Area | Tool |
|---|---|
| Image publish | Docker Hub push of `kirandevraaj/platform-lab` |
| CI | Jenkins |
| CD | Argo CD / GitOps |
| Observability | Prometheus, Grafana, OpenTelemetry |
| AWS path | Terraform |

Docker Desktop client 29.6.1 builds the local image. It is not the cluster runtime. Terraform is not installed.

## Environment strategy

Two deployment targets stay separate for the life of this project.

| Target | Purpose | How it is reached |
|---|---|---|
| Local lab | Day-to-day platform work on the three VMware nodes | SSH and kubectl against `192.168.56.0/24` |
| AWS | A future deployment target, to be defined in Terraform and `kubernetes/overlays/aws` | AWS credentials and a distinct kube context, used only when that phase starts |

When those overlays exist, they will describe the same application shape with different infrastructure. A change for one target stays in that target. See [environment strategy](docs/design/environment-strategy.md).

## Planned implementation phases

1. **Repository baseline.** Project layout, architecture notes, and a read-only record of the current lab. This phase.
2. **Application and image.** The Python service, tests, and local Dockerfile are in `app/`. The image tag `kirandevraaj/platform-lab:0.1.0` is built locally and has not been published.
3. **Kubernetes packaging.** Base manifests and local/AWS overlays, applied only after review.
4. **Jenkins CI.** Build, test, and publish the image.
5. **Argo CD GitOps.** The cluster reconciles from Git.
6. **Networking.** Ingress, service exposure, and NetworkPolicy appropriate to each target.
7. **Observability.** Prometheus, Grafana, and OpenTelemetry for the application.
8. **AWS path.** Terraform for the AWS runtime, kept apart from the VMware lab.
9. **Python automation.** Repeatable checks and operational helpers.

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
├── terraform/
│   └── aws/
└── scripts/
```

## License

MIT. See [LICENSE](LICENSE).
