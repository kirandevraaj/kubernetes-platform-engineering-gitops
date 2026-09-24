# Kubernetes Platform Engineering & GitOps Lab

A portfolio project that builds a small platform around a containerized application: Kubernetes delivery, infrastructure as code, CI, GitOps CD, an AWS deployment path, networking, observability, and Python automation.

## Project objective

Show how a platform engineer takes an application from source to a running Kubernetes workload, with a repeatable local lab and a separate AWS target. Each layer is added only after the previous one is documented and working.

The current lab cluster is an existing three-node environment used as the local runtime. The FastAPI application lives under `app/`, and its container image is published on Docker Hub as `kirandevraaj/platform-lab:0.1.0`. The local overlay is applied on that cluster. The Jenkins pipeline definition is in `jenkins/Jenkinsfile`. Jenkins execution is not configured yet. Terraform resources and Argo CD resources are not included yet.

## Architecture overview

The diagram below is the intended shape. The Python application is containerized and version `0.1.0` is published and running on the local lab. The Jenkins pipeline is defined and has not been executed. Argo CD, Terraform, and the AWS target are not implemented. The local VMware lab is the only Kubernetes runtime that exists today.

```text
Developer
   |
   v
Git repository
   |
   +--> container image (published: kirandevraaj/platform-lab:0.1.0)
   |
   +--> Jenkins CI (defined, not running) --> image build and test
   |
   +--> Argo CD / GitOps (planned) --> Kubernetes
                                          |
                                          +--> local lab (VMware Workstation, current runtime)
                                          |
                                          +--> AWS target (planned, separate)

Observability: Prometheus, Grafana, OpenTelemetry (planned)
Automation: Python (planned)
Infrastructure: Terraform / AWS path (planned)
```

Local runtime observed on 24 September 2026 (read-only):

| Node | Role | Address | OS | Kubernetes | Runtime |
|---|---|---|---|---|---|
| k8s-ctrl-01 | control-plane | 192.168.56.10 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-01 | worker | 192.168.56.11 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |
| k8s-worker-02 | worker | 192.168.56.12 | Ubuntu 24.04.4 LTS | v1.31.14 | containerd 2.2.1 |

Platform components already running in the local cluster: Calico v3.30.7 (CNI), CoreDNS, kube-proxy, metrics-server, ingress-nginx (NodePort 30080/30443), MetalLB, and the local-path provisioner. The application workload `platform-lab` is deployed in namespace `platform-lab` from `kubernetes/overlays/local`: two replicas of `kirandevraaj/platform-lab:0.1.0` and a ClusterIP Service on port 8000. The AWS overlay is not applied.

## Technology stack

Present in the local lab now:

| Area | What is there |
|---|---|
| Local infrastructure | VMware Workstation Pro on Windows 11 |
| Node OS | Ubuntu 24.04.4 LTS |
| Orchestration | Kubernetes v1.31.14 |
| Node runtime | containerd 2.2.1 |
| Networking | Calico v3.30.7, ingress-nginx, MetalLB |
| Application | Python FastAPI service under `app/`, version 0.1.0, running in namespace `platform-lab` on the local cluster |
| Published image | `kirandevraaj/platform-lab:0.1.0` on Docker Hub |

Planned, and not in this repository yet:

| Area | Tool |
|---|---|
| CD | Argo CD / GitOps |
| Observability | Prometheus, Grafana, OpenTelemetry |
| AWS path | Terraform |

The Jenkins pipeline definition is in the repository. The Jenkins controller, job, and Docker Hub credential are not configured yet.

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
2. **Application and container image.** Completed. The service, tests, and Dockerfile are in `app/`. `kirandevraaj/platform-lab:0.1.0` is published. The tag `latest` is not used.
3. **Kubernetes packaging.** Completed. Deployed to the local lab on 24 September 2026. `kubectl apply -k kubernetes/overlays/local` created namespace `platform-lab`, ConfigMap `platform-lab-config`, Deployment `platform-lab` (2/2 ready), and ClusterIP Service `platform-lab`. The AWS overlay has not been applied.
4. **Jenkins CI pipeline definition.** Completed. `jenkins/Jenkinsfile` checks out the repository, tests `app/tests`, reads `APP_VERSION`, builds and validates `kirandevraaj/platform-lab:<APP_VERSION>`, and pushes that tag. See [jenkins/README.md](jenkins/README.md).
5. **Jenkins execution and publishing.** Not yet completed. No Jenkins job or Docker Hub credential has been created, and this pipeline has not run.
6. **Argo CD GitOps.** Planned. The cluster reconciles from Git.
7. **Networking.** Planned. Ingress, service exposure, and NetworkPolicy appropriate to each target.
8. **Observability.** Planned. Prometheus, Grafana, and OpenTelemetry for the application.
9. **AWS path.** Planned. Terraform for the AWS runtime, kept apart from the VMware lab.
10. **Python automation.** Planned. Repeatable checks and operational helpers.

## Published container artifact

Version `0.1.0` is the current published image. It was pushed successfully. The tag `latest` is intentionally unused, so a pull always names `0.1.0`. The digest is the immutable reference for that artifact.

| Field | Value |
|---|---|
| Image | `kirandevraaj/platform-lab:0.1.0` |
| Docker Hub | https://hub.docker.com/r/kirandevraaj/platform-lab |
| Digest | `sha256:e6c16fbebf01422a6a0f0c21b3aebb0991ccca4c3a2af190d0b0ad5f264ba788` |

```text
docker pull kirandevraaj/platform-lab:0.1.0
docker pull kirandevraaj/platform-lab@sha256:e6c16fbebf01422a6a0f0c21b3aebb0991ccca4c3a2af190d0b0ad5f264ba788
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
│   └── README.md
├── terraform/
│   └── aws/
└── scripts/
```

## License

MIT. See [LICENSE](LICENSE).
