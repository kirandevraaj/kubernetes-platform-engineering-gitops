# CI/CD flow

Status: automated CI → Docker Hub → GitOps promotion is implemented in `jenkins/Jenkinsfile`. Argo CD Application `platform-lab-local` remains the only deploy path onto `ckad-lab`. The manual `0.1.1` path was demonstrated first; full automation is loaded by Jenkins after the Jenkinsfile reaches `main`.

## CI and CD

CI builds, tests, packages, publishes an image, and commits the local overlay image tag. It does not call `kubectl`.

CD is Argo CD on the VMware cluster. It reads Git and syncs Kubernetes manifests. Details are in [gitops-flow.md](gitops-flow.md).

### What each layer changes

| Layer | Changes | Does not change |
|---|---|---|
| Jenkins CI (app/** only) | Tests, image build/validation, Docker Hub tag, Git commit to local overlay `newTag` | Live Kubernetes objects directly; AWS overlay |
| Git commit to `kubernetes/overlays/local` | Desired image tag for Argo CD | Docker Hub contents by itself |
| Argo CD | Live cluster objects until they match Git | Image builds or registry pushes |

Publishing a new image is not the same as deploying it. The cluster moves to a new tag only after Git records that tag and Argo CD reconciles. Kubernetes networking objects (Ingress, NetworkPolicy) also change only through Git → Argo CD, not through Jenkins.

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
    |
    +-- app/** --> Unit Test
                   Read APP_VERSION from app/src/__init__.py
                   Refuse if Docker Hub already has that tag
                   Docker Build / Validate / Push
                   Update kubernetes/overlays/local/kustomization.yaml
                   git commit + push (github-platform-lab)
                        |
                        v
                   GitHub main
                        |
                        v
                   Argo CD sync on ckad-lab
```

### Loop prevention

The GitOps promotion commit touches only `kubernetes/overlays/local/kustomization.yaml`. The next poll still starts a build, but Detect Application Change finds no `app/**` files, so Docker and promotion stages are skipped. Concurrent promotions are blocked with `disableConcurrentBuilds()`.

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
- It does not promote `kubernetes/overlays/aws`.
- It does not reuse or overwrite an existing Docker Hub version tag.

## CD path

Argo CD Application `platform-lab-local` renders `kubernetes/overlays/local` and converges namespace `platform-lab` on `ckad-lab`. An AWS Application does not exist yet.

## Manual integration test: 0.1.1 (24 September 2026)

Before automation, the same path was exercised by hand:

1. Application release commit `7557521` (`0.1.1`, release `ci-cd-integration-test`).
2. Jenkins published `kirandevraaj/platform-lab:0.1.1` (digest `sha256:820a90907dbd09e650acaea652dd48741ef36849b34c581bc2732dc7cb8eba8c`).
3. GitOps commit `a8ca030` set the local overlay tag to `0.1.1`.
4. Argo CD synced without `kubectl apply`.
5. Pods ran `0.1.1`; `GET /` showed version `0.1.1`, environment `local-gitops`, release `ci-cd-integration-test`.

## Automation status

| Item | State |
|---|---|
| Jenkinsfile automation | Implemented and loaded (`pollSCM`, app/** gate, promote + push) |
| Controlled automated release demo | **Completed** for `0.1.2` on 24 September 2026 |

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