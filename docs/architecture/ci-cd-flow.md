# CI/CD flow

Status: CI and CD are both live for the local lab. Job `platform-lab-ci` publishes images to Docker Hub. Argo CD Application `platform-lab-local` reconciles `kubernetes/overlays/local` onto `ckad-lab`. The manual `0.1.1` integration test completed successfully on 24 September 2026.

## CI and CD

CI builds, tests, packages, and publishes an image. It stops at Docker Hub.

CD is Argo CD on the VMware cluster. It reads Git and syncs Kubernetes manifests. Details are in [gitops-flow.md](gitops-flow.md).

Jenkins does not run `kubectl apply` as the deploy step.

### What each layer changes

| Layer | Changes | Does not change |
|---|---|---|
| Jenkins CI | Application tests, image build, image validation, Docker Hub tag `kirandevraaj/platform-lab:<APP_VERSION>` | Live Kubernetes objects, Argo CD Application desired revision, overlay image tag in Git |
| Git commit to `kubernetes/overlays/local` | Desired Kubernetes state in Git (for example the image tag Argo CD should sync) | Docker Hub contents by itself |
| Argo CD | Live cluster objects until they match Git | Image builds or registry pushes |

Publishing a new image is not the same as deploying it. The cluster moves to a new tag only after Git records that tag and Argo CD reconciles.

## CI path

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

`APP_VERSION` is read from `app/src/__init__.py`. The current value is `0.1.1`, so CI publishes `kirandevraaj/platform-lab:0.1.1`. The tag `latest` is not used.

The Docker Hub token is Jenkins credential `dockerhub-platform-lab`. It is not stored in Git. Image validation attaches a temporary container to the agent Compose network and probes `/health` by container DNS name. A published host loopback port is incorrect for this socket-mounted agent layout and is not used.

## Local Jenkins runtime

The controller and the build agent run on Docker Desktop, on the Compose network `platform-lab-jenkins`. They do not run on the VMware nodes. Docker Desktop Kubernetes stays disabled.

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

Argo CD Application `platform-lab-local` renders `kubernetes/overlays/local` and converges namespace `platform-lab` on `ckad-lab`. An AWS Application for `kubernetes/overlays/aws` does not exist yet. The workload was first applied with `kubectl apply -k`; Argo CD now owns ongoing reconciliation from Git. The `0.1.1` promotion used Git and Argo CD only—no manual `kubectl apply`.

## Manual integration test: 0.1.1 (24 September 2026)

End-to-end path exercised:

1. **Application release.** Commit `7557521` set `APP_VERSION` to `0.1.1` and added `release: ci-cd-integration-test` on `GET /`.
2. **CI publish.** Jenkins job `platform-lab-ci` built, tested, validated, and pushed `kirandevraaj/platform-lab:0.1.1` (digest `sha256:820a90907dbd09e650acaea652dd48741ef36849b34c581bc2732dc7cb8eba8c`).
3. **GitOps desired state.** Commit `a8ca030` updated only `kubernetes/overlays/local/kustomization.yaml` so Kustomize resolves the image to `0.1.1`. Base and AWS overlay stayed on `0.1.0`.
4. **CD reconcile.** Argo CD detected the Git change and synced Application `platform-lab-local`. No `kubectl apply` was used for the promotion.
5. **Cluster result.** Rollout completed. Both pods ran `kirandevraaj/platform-lab:0.1.1`.
6. **HTTP checks.** `GET /` returned version `0.1.1`, environment `local-gitops`, and release `ci-cd-integration-test`. `GET /version`, `/health`, and `/info` returned HTTP 200.
