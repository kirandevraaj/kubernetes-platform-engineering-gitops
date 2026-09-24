# Jenkins CI

Status: automated CI/CD is demonstrated end-to-end. Job `platform-lab-ci` polls GitHub (`H/2 * * * *`), builds only when `app/**` changes, published `kirandevraaj/platform-lab:0.1.2` on build `#5`, and promoted the local overlay. Build `#6` confirmed the GitOps commit does not rebuild the image. Promotion updates only the `newTag` field in `kubernetes/overlays/local/kustomization.yaml` so other overlay resources (ingress Service patch, ServiceMonitor, patches) are preserved.

## Local runtime

Jenkins runs on Docker Desktop. It does not run on `k8s-ctrl-01`, `k8s-worker-01`, or `k8s-worker-02`. Those VMs are the Project 1 Kubernetes cluster. Docker Desktop Kubernetes is disabled. The Linux engine stays enabled.

| Piece | Value |
|---|---|
| Controller image | `jenkins/jenkins:2.568.3-lts-jdk21` (Jenkins 2.568.3 LTS from the Jenkins download page) |
| Built controller | `platform-lab-jenkins-controller:2.568.3` |
| Agent base | `jenkins/inbound-agent:3391.va_37fa_a_305d6d-3-jdk21` |
| Built agent | `platform-lab-jenkins-agent:1` |
| UI | http://127.0.0.1:8080 |
| JENKINS_HOME | Docker volume `platform-lab-jenkins-home` |
| Network | `platform-lab-jenkins` |
| Agent TCP port 50000 | Not published |

Compose file: `jenkins/runtime/compose.yaml`.

```powershell
docker compose -f jenkins/runtime/compose.yaml up -d
```

That command starts the controller only. The agent is behind the Compose profile `agent` and is not started until you create the node in the UI.

### Plugins

`jenkins/runtime/controller/plugins.txt` requests three plugins. `jenkins-plugin-cli` also installs the dependencies those plugins require.

| Plugin | Why it is here |
|---|---|
| `workflow-aggregator` | Declarative Pipeline, including `sh` steps |
| `git` | `checkout scm` |
| `credentials-binding` | `withCredentials` and `usernamePassword` |

WebSocket inbound agents are part of this Jenkins LTS core. No extra agent plugin is installed. The setup wizard is left enabled. This repository does not set an administrator password.

### Agent

The agent container is a separate Linux image. It has Java 21, bash, sh, git, Python 3, pip, `python3 -m venv`, CA certificates, and the Docker CLI 29.6.1. It does not contain a Docker daemon.

When you start it later, Compose mounts `/var/run/docker.sock` from Docker Desktop. The entrypoint adds the `jenkins` user to the socket's group, then runs `jenkins-agent` as that user with `JENKINS_WEB_SOCKET=true`. On this Docker Desktop engine the socket group is root, so the user is added to that group for the life of the container.

Giving the agent the Docker socket lets a job start, stop, and remove containers on this Docker Desktop engine, and build images with the host daemon. That is acceptable on this isolated personal lab. It is not a pattern to copy onto a shared build host. Docker-in-Docker is not used.

Create the node yourself. Suggested values for this lab:

| Field | Value |
|---|---|
| Name | `linux-agent` |
| Executors | 1 |
| Labels | `linux docker` |
| Remote root directory | `/home/jenkins/agent` |
| Launch method | Launch agent by connecting it to the controller |
| WebSocket | Enabled |

Copy the node secret from the UI. Do not commit it. Then, from the repository root:

```powershell
$env:JENKINS_AGENT_SECRET = "<secret from the node page>"
docker compose -f jenkins/runtime/compose.yaml --profile agent up -d agent
```

`JENKINS_AGENT_SECRET` is empty in Compose unless you set it in the shell. The agent will not connect without that value.

### Manual setup still required

Open http://127.0.0.1:8080. Jenkins shows the initial unlock screen. The one-time unlock password is in the controller at `/var/jenkins_home/secrets/initialAdminPassword`. Read it from the running container. Do not store it in Git.

```powershell
docker exec platform-lab-jenkins-controller-1 cat /var/jenkins_home/secrets/initialAdminPassword
```

Then, in the UI:

1. Paste the unlock password.
2. Create the first administrator account.
3. Finish the setup wizard. The image already contains the plugins above. You do not need to install a suggested plugin bundle if the wizard offers one.
4. Confirm Pipeline, Git, and Credentials Binding are installed.
5. Create the `linux-agent` node with the values above, then start the agent profile.

Credentials created in Jenkins (not in Git):

| ID | Purpose |
|---|---|
| `dockerhub-platform-lab` | Docker Hub push |
| `github-platform-lab` | GitOps promotion push to `origin/main` |

## Purpose

Jenkins is the continuous integration system for `platform-lab`. It builds, tests, and publishes the container image, then writes the new tag into the local GitOps overlay. It does not deploy to Kubernetes. Desired cluster state is reconciled by Argo CD after the promotion commit lands on `main`.

## Automated flow

```text
pollSCM (H/2 * * * *)
        |
        v
Detect Application Change  (app/** only)
        |
        +-- no app/** --> SUCCESS, skip remaining CI/CD stages
        |
        +-- app/** --> Unit Test
                       Read APP_VERSION
                       Refuse existing Docker Hub tag
                       Docker Build
                       Docker Image Validation
                       Docker Hub Push
                       Promote GitOps (local kustomization only)
                       Git Push (github-platform-lab)
```

Polling is intentional for this lab. No GitHub webhook is configured.

### Loop prevention

The promotion commit changes only `kubernetes/overlays/local/kustomization.yaml`. The next poll still runs the job, but **Detect Application Change** sees no `app/**` path in the SCM change set, so build/push/promotion stages are skipped. The build remains SUCCESS.

`disableConcurrentBuilds()` prevents two promotions from racing.

### Version and image rules

| Rule | Behavior |
|---|---|
| Version source | `APP_VERSION` in `app/src/__init__.py` only |
| Image | `kirandevraaj/platform-lab:<APP_VERSION>` |
| `latest` | Never built or pushed |
| Existing Hub tag | Build fails rather than overwriting |

### GitOps promotion

Jenkins rewrites `kubernetes/overlays/local/kustomization.yaml` to:

```yaml
images:
  - name: kirandevraaj/platform-lab
    newTag: "<APP_VERSION>"
```

It does not edit `kubernetes/base/**`, `kubernetes/overlays/aws/**`, or `gitops/**`. The commit author is `Jenkins CI <jenkins-ci@local>`. Push uses credential `github-platform-lab` through a temporary `GIT_ASKPASS` helper (token not written into remotes or files).

## Pipeline stages

| Stage | What it does |
|---|---|
| Checkout | `checkout scm` |
| Detect Application Change | Sets `APP_CHANGED` from the SCM change set (`app/**`) |
| Unit Test | Creates `.venv`, installs `app/requirements-dev.txt`, runs pytest (app changes only) |
| Read Application Version | Parses `APP_VERSION` from `app/src/__init__.py` |
| Refuse Existing Image Tag | Fails if `kirandevraaj/platform-lab:<APP_VERSION>` already exists on Docker Hub |
| Docker Build | `docker build -f app/Dockerfile -t kirandevraaj/platform-lab:<APP_VERSION> app` |
| Docker Image Validation | Inspects image metadata, runs a one-shot import check, then `/health` over the agent Docker network; removes the temporary container |
| Docker Hub Push | Logs in with `dockerhub-platform-lab`, pushes the version tag, prints the image digest |
| Promote GitOps | Updates only the local overlay image tag |
| Git Push | Fast-forwards to `origin/main`, commits, pushes with `github-platform-lab` |

### Image validation networking

The agent talks to Docker Desktop through `/var/run/docker.sock`. Published host ports bind on the Docker Desktop VM, not in the agent namespace. Validation attaches the temporary container to the agent Compose network and probes `http://<container-name>:8000/health`.

## Secrets stay in Jenkins

Git stores the pipeline and credential IDs. Jenkins Credentials stores tokens. A clone of this repository cannot log in to Docker Hub or push to GitHub as the CI identity.

## Artifact flow

```text
app/** change on main
        |
        v
Jenkins unit tests + image build
        |
        v
Docker Hub kirandevraaj/platform-lab:<APP_VERSION>
        |
        v
Git commit: local overlay newTag=<APP_VERSION>
        |
        v
Argo CD sync on ckad-lab
```

AWS is intentionally outside this automation. The AWS overlay keeps its own image tag until a separate promotion path exists.
