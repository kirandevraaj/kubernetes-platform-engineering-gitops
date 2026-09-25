# CI/CD flow

Status: automated CI → Docker Hub → **multi-environment** GitOps promotion is implemented in `jenkins/Jenkinsfile`. Argo CD Application `platform-lab-local` deploys to VMware (`ckad-lab`). Argo CD Application `platform-lab-aws` (Terraform-bootstrapped on EKS) deploys to AWS. Jenkins never deploys with `kubectl`.

**Jenkins performs CI and GitOps promotion. Argo CD performs Kubernetes deployment and reconciliation.**

## CI and CD

CI builds, tests, packages, publishes an image, and commits the image tag into **both** overlays (`kubernetes/overlays/local` and `kubernetes/overlays/aws`). It does not call `kubectl`.

CD is Argo CD on each target cluster. It reads Git and syncs Kubernetes manifests. Details are in [gitops-flow.md](gitops-flow.md) and [gitops/README.md](../../gitops/README.md).

### What each layer changes

| Layer | Changes | Does not change |
|---|---|---|
| Jenkins CI (app/** only) | Tests, image build/validation, Docker Hub tag, Git commit to local + aws overlay `newTag` | Live Kubernetes objects directly; Terraform; environment-specific patches |
| Git commit to overlays | Desired image tag for both Argo CD Applications | Docker Hub contents by itself |
| Argo CD (`platform-lab-local`) | Live objects on VMware until they match Git | Image builds |
| Argo CD (`platform-lab-aws`) | Live objects on EKS until they match Git | Image builds |

Publishing a new image is not the same as deploying it. Each cluster moves to a new tag only after Git records that tag and that cluster's Argo CD reconciles. Kubernetes networking objects (Ingress, NetworkPolicy) also change only through Git → Argo CD, not through Jenkins.

## Automated path

```text
Developer pushes app/** to main
    |
    v
Jenkins pollSCM (H/2 * * * *)
    |
    v
Detect Application Change
    |-- no app/** --> SUCCESS (skip build/push/promote)
    |     docs / terraform / GitOps-only / jenkins-only / etc.
    |
    +-- app/** --> Unit Test
                   Read APP_VERSION from app/src/__init__.py
                   Refuse if Docker Hub already has that tag
                   Docker Build / Validate / Push
                   Update kubernetes/overlays/local/kustomization.yaml
                   Update kubernetes/overlays/aws/kustomization.yaml
                   git commit + push (github-platform-lab)
                        |
                        v
                   GitHub main
                        |
                        +--> Argo CD platform-lab-local → VMware
                        |
                        +--> Argo CD platform-lab-aws   → EKS
```

### Loop prevention

The GitOps promotion commit touches only overlay `kustomization.yaml` image `newTag` fields (local and/or aws). The next poll still starts a build, but Detect Application Change finds no `app/**` files, so Docker and promotion stages are skipped. Concurrent promotions are blocked with `disableConcurrentBuilds()`.

### Triggers

This lab uses `pollSCM('H/2 * * * *')` on purpose. No GitHub webhook is configured in this step.

## Version and image

`APP_VERSION` is read from `app/src/__init__.py` only. The image is always `kirandevraaj/platform-lab:<APP_VERSION>`. The tag `latest` is never built or pushed. An already-published version tag fails the build.

Credentials (Jenkins only, not in Git):

| ID | Use |
|---|---|
| `dockerhub-platform-lab` | `docker login --password-stdin` for push |
| `github-platform-lab` | Temporary `GIT_ASKPASS` for `git push origin HEAD:main` |

Image validation attaches a temporary container to the agent Compose network and probes `/health` by container DNS name.

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

Details are in [jenkins/README.md](../../jenkins/README.md).

## What CI does not do

- It does not edit the live cluster with `kubectl`.
- It does not install or operate Argo CD.
- It does not modify Terraform, AWS infrastructure, or environment-specific overlay patches.
- It does not reuse or overwrite an existing Docker Hub version tag.

## CD path

| Application | Overlay | Destination |
|---|---|---|
| `platform-lab-local` | `kubernetes/overlays/local` | VMware `ckad-lab` (in-cluster API) |
| `platform-lab-aws` | `kubernetes/overlays/aws` | EKS `platform-lab-aws-lab-eks` (in-cluster API; Terraform-bootstrapped) |

## Next release milestone

Bump `APP_VERSION` to `0.1.4` in `app/src/__init__.py`, push an `app/**` commit to `main`, and verify Jenkins publishes `:0.1.4` then promotes both overlays. Do not bump the version until that release milestone starts.

## Manual integration test: 0.1.1 (24 September 2026)

Before automation, the same path was exercised by hand (local overlay only at that time):

1. Application release commit `7557521` (`0.1.1`, release `ci-cd-integration-test`).
2. Jenkins published `kirandevraaj/platform-lab:0.1.1` (digest `sha256:820a90907dbd09e650acaea652dd48741ef36849b34c581bc2732dc7cb8eba8c`).
3. GitOps commit `a8ca030` set the local overlay tag to `0.1.1`.
4. Argo CD synced without `kubectl apply`.
5. Pods ran `0.1.1`; `GET /` showed version `0.1.1`, environment `local-gitops`, release `ci-cd-integration-test`.

## Automation status

| Item | State |
|---|---|
| Jenkinsfile automation | Implemented (`pollSCM`, app/** gate, dual-overlay promote + push) |
| Local automated release demo | **Completed** for `0.1.2` / `0.1.3` on the VMware path |
| Multi-environment promotion | **Implemented** in Jenkinsfile; first dual release demo deferred to `0.1.4` |

## Automated integration test: 0.1.2 (24 September 2026)

| Step | Evidence |
|---|---|
| Application commit | `d7e0a12` — `feat: release platform-lab 0.1.2 for automated CI/CD test` (`release: automated-ci-cd`) |
| Seed / non-app build | Jenkins `#4` SUCCESS — CI/CD stages skipped (Jenkinsfile/docs only) |
| App CI/CD build | Jenkins `#5` — Started by SCM change — SUCCESS on `linux-agent` |
| Image | `kirandevraaj/platform-lab:0.1.2` |
| Digest | `sha256:082e161b0c90d588fe4f045d80a54297881e188a0e6417e71aaa814a66b92c8a` |
| GitOps promotion commit | `1eb1428` — `chore: promote platform-lab 0.1.2 to local GitOps` (only local kustomization) |
| Loop-prevention build | Jenkins `#6` — SCM change on kustomization only — SUCCESS with stages skipped |
| Argo CD | Synced / Healthy on revision `1eb1428` (after refresh; Progressing during rollout) |
| Deployment | `platform-lab` 2/2 Ready, image `0.1.2`; prior `0.1.1` ReplicaSet scaled to 0 |
| HTTP | `GET /` → version `0.1.2`, environment `local-gitops`, release `automated-ci-cd`; `/health`, `/version`, `/info` → 200 |

No manual `kubectl apply`, `docker build`, or `docker push` was used for the `0.1.2` promotion path.