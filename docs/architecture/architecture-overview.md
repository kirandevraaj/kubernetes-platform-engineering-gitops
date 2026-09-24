# Architecture overview

Status: baseline. This document records the lab as observed and the platform shape we intend to build. It does not authorize changes.

## Current local runtime

Three Ubuntu 24.04.4 LTS virtual machines on VMware Workstation Pro, on host-only network `192.168.56.0/24`. This is the current development environment:

| Node | Role | Address |
|---|---|---|
| k8s-ctrl-01 | control-plane | 192.168.56.10 |
| k8s-worker-01 | worker | 192.168.56.11 |
| k8s-worker-02 | worker | 192.168.56.12 |

Kubernetes v1.31.14. Container runtime is containerd 2.2.1. Control-plane components run as static pods on `k8s-ctrl-01` (`etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`).

## Cluster platform already present

| Concern | Component |
|---|---|
| CNI | Calico v3.30.7, installed with the Tigera operator (`calico-system`, `calico-apiserver`, `tigera-operator`) |
| DNS | CoreDNS |
| Node proxy | kube-proxy |
| Metrics | metrics-server |
| Ingress | ingress-nginx, Service type NodePort `80:30080` and `443:30443` |
| Load balancer addresses | MetalLB (`controller` plus `speaker` on each node) |
| Storage | local-path provisioner (`local-path-storage`) |

No application namespace or application workload was present during the read-only check. Namespaces in use: `calico-apiserver`, `calico-system`, `default`, `ingress-nginx`, `kube-node-lease`, `kube-public`, `kube-system`, `local-path-storage`, `metallb-system`, `tigera-operator`.

## Planned platform shape

The repository will hold one application, packaged once, and deployed through two overlays:

- `kubernetes/overlays/local` for this VMware cluster
- `kubernetes/overlays/aws` for a later AWS cluster

None of that is built yet. Jenkins is planned to build and test the image. Argo CD is planned to deploy from Git. Prometheus, Grafana, and OpenTelemetry are planned to observe the application after it exists. Terraform under `terraform/aws` is reserved for the AWS path and does not describe this VMware lab. AWS is a separate future deployment target.

## Windows workstation

The workstation reaches the nodes with OpenSSH (`k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02` in the user SSH config). A local kubectl context named `ckad-lab` is present. Docker Desktop client 29.6.1 is installed; the engine was not running at assessment time. Terraform is not on `PATH`.
