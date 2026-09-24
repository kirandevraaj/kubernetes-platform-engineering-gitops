# CI/CD flow

Status: CI and CD are both live for the local lab. Job `platform-lab-ci` publishes images to Docker Hub. Argo CD Application `platform-lab-local` reconciles `kubernetes/overlays/local` onto `ckad-lab`.

## CI and CD

CI builds, tests, packages, and publishes an image. It stops at Docker Hub.

CD is Argo CD on the VMware cluster. It reads Git and syncs Kubernetes manifests. Details are in [gitops-flow.md](gitops-flow.md).

Jenkins does not run `kubectl apply` as the deploy step.

## Intended CI path

```text
Developer
    |
    v
GitHub
    |
    v
Jenkins CI
    |-- Checkout
    |-- Unit Test
    |-- Read Application Version
    |-- Docker Build
    |-- Docker Image Validation
    |-- Docker Hub Push
            |
            v
      Docker Hub
      kirandevraaj/platform-lab:<APP_VERSION>
```

`APP_VERSION` is read from `app/src/__init__.py`. The current value is `0.1.0`, so the image name is `kirandevraaj/platform-lab:0.1.0`. The tag `latest` is not used.

The Docker Hub token is Jenkins credential `dockerhub-platform-lab`. It is not stored in Git. Image validation attaches a temporary container to the agent Compose network and probes `/health` by container DNS name. A published host loopback port is incorrect for this socket-mounted agent layout and is not used.

## Local Jenkins runtime

The controller and the future build agent run on Docker Desktop, on the Compose network `platform-lab-jenkins`. They do not run on the VMware nodes. Docker Desktop Kubernetes stays disabled.

```text
Windows workstation
    |
    v
Docker Desktop Linux engine
    |-- Jenkins controller (127.0.0.1:8080)
    |       JENKINS_HOME volume: platform-lab-jenkins-home
    |
    \-- Linux agent (online, labels linux docker)
            WebSocket to the controller
            Docker CLI via /var/run/docker.sock
```

The agent socket mount can control the Docker Desktop engine. That is limited to this personal lab. Details are in [jenkins/README.md](../../jenkins/README.md).

## What CI does not do

- It does not edit the live cluster.
- It does not install or operate Argo CD.
- It does not change Kubernetes desired state in Git. Recording a new image tag in `kubernetes/` remains a separate commit that Argo CD then syncs.
- It does not publish one image for the local lab and another for AWS. Both targets use the same versioned image name until an AWS registry is introduced.

## CD path

Argo CD Application `platform-lab-local` renders `kubernetes/overlays/local` and converges namespace `platform-lab` on `ckad-lab`. An AWS Application for `kubernetes/overlays/aws` does not exist yet. The workload was first applied with `kubectl apply -k`; Argo CD now owns ongoing reconciliation from Git.
