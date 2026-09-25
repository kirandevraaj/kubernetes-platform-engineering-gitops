# Jenkins CI

Status: automated multi-environment CI/CD promotion is implemented. Job `platform-lab-ci` polls GitHub (`H/2 * * * *`), builds only when `app/**` changes, publishes `kirandevraaj/platform-lab:<APP_VERSION>`, captures the registry-published digest, and promotes **both** GitOps overlays with that immutable digest plus `app.kubernetes.io/version`. GitOps-only promotion commits skip rebuild (loop prevention).

**Jenkins performs CI and GitOps promotion. Argo CD performs Kubernetes deployment and reconciliation.**

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

Jenkins is the continuous integration system for `platform-lab`. It builds, tests, and publishes the container image, then writes the **immutable digest** and release version label into **both** GitOps overlays. It does not deploy to Kubernetes (`kubectl apply` / `kubectl set image` / `helm upgrade` are not used against the application). Desired cluster state is reconciled by Argo CD after the promotion commit lands on `main`.

| Environment | Overlay | Argo CD Application | Cluster |
|---|---|---|---|
| Local / VMware | `kubernetes/overlays/local` | `platform-lab-local` | `ckad-lab` |
| AWS / EKS | `kubernetes/overlays/aws` | `platform-lab-aws` | `platform-lab-aws-lab-eks` |

## Automated flow

```text
pollSCM (H/2 * * * *)
        |
        v
Detect Application Change  (app/** only)
        |
        +-- no app/** --> SUCCESS, skip remaining CI/CD stages
        |     (docs-only, terraform-only, GitOps-only, jenkins-only, etc.)
        |
        +-- app/** --> Unit Test
                       Read APP_VERSION
                       Refuse existing Docker Hub tag
                       Docker Build
                       Docker Image Validation
                       Docker Hub Push
                       Capture Published Digest  (mandatory; fail closed)
                       Promote Local GitOps  (local digest + version label)
                       Promote AWS GitOps    (same digest + version label)
                       Commit and Push GitOps (github-platform-lab)
                                |
                                v
                       Argo CD
                        ├── platform-lab-local → VMware
                        └── platform-lab-aws   → EKS
```

Polling is intentional for this lab. No GitHub webhook is configured.

### Loop prevention

The promotion commit changes only overlay `kustomization.yaml` files under `kubernetes/overlays/{local,aws}/` (image `digest` + version label). The next poll still runs the job, but **Detect Application Change** sees no `app/**` path in the SCM change set, so build/push/promotion stages are skipped. The build remains SUCCESS.

The same skip applies to documentation-only, Terraform-only, and other non-`app/**` commits.

`disableConcurrentBuilds()` prevents two promotions from racing.

### Version and image rules

| Rule | Behavior |
|---|---|
| Version source | `APP_VERSION` in `app/src/__init__.py` only |
| Registry tag (push) | `kirandevraaj/platform-lab:<APP_VERSION>` |
| GitOps image pin | `kirandevraaj/platform-lab@sha256:<digest>` |
| Version metadata | `app.kubernetes.io/version: "<APP_VERSION>"` |
| `latest` | Never built or pushed |
| Existing Hub tag | Build fails rather than overwriting |
| Missing digest | Build fails; GitOps is not updated |

The release version identifies the logical release.
The container digest identifies the immutable artifact.

Example for the current logical release `0.1.4`:

| Kind | Reference |
|---|---|
| Tag-based release | `kirandevraaj/platform-lab:0.1.4` |
| Immutable artifact | `kirandevraaj/platform-lab@sha256:<digest>` |

### GitOps promotion

Jenkins rewrites both overlays so the **same** published digest and Kubernetes version metadata stay aligned with `APP_VERSION` from `app/src/__init__.py`:

```yaml
images:
  - name: kirandevraaj/platform-lab
    digest: sha256:<published-digest>
labels:
  - pairs:
      app.kubernetes.io/version: "<APP_VERSION>"
    includeSelectors: false
    includeTemplates: true
```

Rendered container image: `kirandevraaj/platform-lab@sha256:<published-digest>`.

There is no second application version source. Base manifests may still contain scaffold `0.1.0` values; overlays override them during render.

It does not edit `kubernetes/base/**`, environment-specific patches (MetalLB, ALB, NetworkPolicy, HPA/PDB), Terraform, or `gitops/**` Application definitions. The commit author is `Jenkins CI <jenkins-ci@local>`. Push uses credential `github-platform-lab` through a temporary `GIT_ASKPASS` helper (token not written into remotes or files). Promotion aligns the two overlay files with `origin/main` via `git checkout origin/main -- <files>` (no `git reset --hard`, no force push).

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
| Docker Hub Push | Logs in with `dockerhub-platform-lab`, pushes the version tag |
| Capture Published Digest | Reads registry `RepoDigests` after push; fails if missing/invalid; sets `IMAGE_DIGEST` |
| Promote Local GitOps | Updates local overlay `digest` + version label |
| Promote AWS GitOps | Updates aws overlay with the **same** `digest` + version label; verifies only overlay kustomizations changed |
| Commit and Push GitOps | Commits both overlays and pushes with `github-platform-lab` |

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
Capture published digest sha256:...
        |
        v
Git commit: local + aws overlay digest=<same> + version=<APP_VERSION>
        |
        +--> Argo CD platform-lab-local  → VMware / ckad-lab
        |
        +--> Argo CD platform-lab-aws    → EKS
```

## Next digest-pinned application release

After this hardening lands on `main`, the next application release should bump `APP_VERSION` under `app/` (for example to `0.1.5`), push an `app/**` commit, and let Jenkins publish the new tag, capture the digest, and promote both overlays. Do not bump the version until that release milestone starts. This milestone does not publish a new application version.
