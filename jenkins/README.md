# Jenkins CI

Status: pipeline definition only. Jenkins is not installed or configured for this repository yet. No job, credential, or controller change has been made. The pipeline has not been executed.

## Purpose

Jenkins is the continuous integration system for `platform-lab`. It builds, tests, and publishes the container image. It does not deploy to Kubernetes. Deployment from Git is a later Argo CD phase.

## CI responsibilities

The pipeline in `jenkins/Jenkinsfile` does this work:

1. Check out the repository.
2. Run the existing pytest suite in `app/tests`.
3. Read `APP_VERSION` from `app/src/__init__.py`.
4. Build `kirandevraaj/platform-lab:<APP_VERSION>` from `app/Dockerfile` with context `app/`.
5. Inspect the image and run a localhost-only health check.
6. Push that one tag to Docker Hub.

A failing test or a failed image check stops the pipeline before the push.

## Pipeline stages

| Stage | What it does |
|---|---|
| Checkout | `checkout scm` |
| Unit Test | Creates `.venv`, installs `app/requirements-dev.txt`, runs `python -m pytest app/tests` |
| Read Application Version | Parses the `APP_VERSION` assignment in `app/src/__init__.py` |
| Docker Build | `docker build -f app/Dockerfile -t kirandevraaj/platform-lab:<APP_VERSION> app` |
| Docker Image Validation | Checks repository and tag, user `app`, port 8000, healthcheck, and `/app/src` files, then curls `/health` on `127.0.0.1:18000` and removes the temporary container |
| Docker Hub Push | Logs in with the Jenkins credential and pushes `kirandevraaj/platform-lab:<APP_VERSION>` |

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

The agent that eventually runs this Jenkinsfile needs:

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

Current source resolves to `kirandevraaj/platform-lab:0.1.0`. There is no second version constant in the pipeline.

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
