# Jenkins CI

Status: CI publishes versioned images from `main` on node `linux-agent`. Credential `dockerhub-platform-lab` is present in Jenkins only. The first successful publish was build `#2` for `0.1.0`. The `0.1.1` integration release was also built and pushed by the same job before GitOps promotion.

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

The Docker Hub credential `dockerhub-platform-lab`, the `linux-agent` node, and the Pipeline job `platform-lab-ci` were created manually in Jenkins. The job points at this repository's `main` branch and script path `jenkins/Jenkinsfile`.

## Purpose

Jenkins is the continuous integration system for `platform-lab`. It builds, tests, and publishes the container image. It does not deploy to Kubernetes. Desired cluster state, including which image tag the Deployment should run, is changed in Git and reconciled by Argo CD.

## CI responsibilities

The pipeline in `jenkins/Jenkinsfile` does this work:

1. Check out the repository.
2. Run the existing pytest suite in `app/tests`.
3. Read `APP_VERSION` from `app/src/__init__.py`.
4. Build `kirandevraaj/platform-lab:<APP_VERSION>` from `app/Dockerfile` with context `app/`.
5. Inspect the image and run `/health` on a temporary container attached to the agent Docker network.
6. Push that one tag to Docker Hub.

A failing test or a failed image check stops the pipeline before the push.

## Pipeline stages

| Stage | What it does |
|---|---|
| Checkout | `checkout scm` |
| Unit Test | Creates `.venv`, installs `app/requirements-dev.txt`, runs `python -m pytest app/tests` |
| Read Application Version | Parses the `APP_VERSION` assignment in `app/src/__init__.py` |
| Docker Build | `docker build -f app/Dockerfile -t kirandevraaj/platform-lab:<APP_VERSION> app` |
| Docker Image Validation | Checks repository and tag, user `app`, port 8000, healthcheck, and `/app/src` files, then requests `/health` on the temporary container over the agent Docker network and removes it |
| Docker Hub Push | Logs in with the Jenkins credential and pushes `kirandevraaj/platform-lab:<APP_VERSION>` |

### Image validation networking

The agent container talks to the Docker Desktop daemon through `/var/run/docker.sock`. A published port such as `-p 127.0.0.1:18000:8000` binds on the Docker Desktop VM, not inside the agent network namespace. The first CI run failed when the validation stage probed that published localhost address from the agent.

The pipeline therefore attaches the temporary container to the same Compose network as the agent (`platform-lab-jenkins`) and requests `http://<container-name>:8000/health` by Docker DNS. A `trap` removes the temporary container when the stage exits. No host port publish is required for this check.

## Docker Hub credential

The Jenkinsfile does not contain a Docker Hub username, password, or access token.

A Jenkins administrator creates a separate **Username with password** credential:

| Field | Value |
|---|---|
| Credentials ID | `dockerhub-platform-lab` |
| Username | Docker Hub account that can push `kirandevraaj/platform-lab` |
| Password | Docker Hub access token for that account |

The push stage binds that credential with `usernamePassword` and passes the token to `docker login --password-stdin`. The token is not written into the repository and is not echoed by the pipeline script. `docker logout` runs after the push and again if the stage exits early.

Do not create this credential in Git. Do not commit a Jenkins home directory, a `credentials.xml`, or a token file.

## Required tools

The `linux-agent` node that runs this Jenkinsfile needs:

| Tool | Use |
|---|---|
| `python3` (or `python`) | Virtual environment, pytest, and reading `APP_VERSION` |
| `pip` | Installed with that Python, used as `python -m pip` |
| Docker Engine and `docker` CLI | Build, inspect, temporary run, and push |

The shell steps use `sh`, so the agent is a Linux agent, or an agent whose default shell can run that syntax. The virtual environment path `.venv/bin/activate` matches that agent. The workstation `.venv` is not the CI environment.

## Secrets stay in Jenkins

Git stores the pipeline and the credential ID. Jenkins Credentials stores the token, encrypted on the controller. A clone of this repository cannot log in to Docker Hub. Rotating the token is a Jenkins credential update, not a commit.

## Image name

| Piece | Source |
|---|---|
| Repository | `IMAGE_REPO` in the Jenkinsfile: `kirandevraaj/platform-lab` |
| Tag | `APP_VERSION` in `app/src/__init__.py` |

Current source resolves to `kirandevraaj/platform-lab:0.1.1`. There is no second version constant in the pipeline.

The tag `latest` is not built or pushed. A moving tag hides which source revision is running. The pipeline stops if `APP_VERSION` is `latest` or if the built image also carries a `latest` tag.

## Artifact flow

```text
app/src and app/tests
        |
        v
Jenkins unit tests
        |
        v
Image kirandevraaj/platform-lab:<APP_VERSION>
        |
        v
Docker Hub
```

Publishing the image does not change the cluster. The running local workload keeps the image reference already declared in `kubernetes/`. A later change to that reference, and Argo CD reconciliation, are separate from this pipeline.
