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

### Why `jenkins/Jenkinsfile` still has `|| true`

Each remaining `|| true` is followed by an explicit check or guards a step whose failure cannot hide a broken build:

| Line pattern | Why it may not fail the stage |
|---|---|
| `docker rm -f "$name" ... \|\| true` (cleanup trap and pre-run) | The validation container may not exist yet; removing a missing container is not an error |
| `docker logout ... \|\| true` (post `always`) | Idempotent logout after the push stage, including when login never happened |
| `full="$(docker image inspect ... \|\| true)"` | An empty value is caught on the next line and fails the build (`Published digest missing`) |
| `git diff -- ... \|\| true` | Informational diff output only |
| `other="$(git diff --name-only \| grep -v ... \|\| true)"` | `grep -v` exits 1 when there are no unexpected files (the success case); a non-empty result fails the build |

## Automation lab pipeline (`Jenkinsfile.automation-lab`)

A separate, manually started job for the Python/Ansible automation in `automation/`. It has no `triggers` block, so it never runs on a commit. Only `platform-lab-ci` polls Git. A merge that changes no `app/**` path still starts a `platform-lab-ci` build on the next poll; **Detect Application Change** then skips build, push and promotion, and the build ends SUCCESS without touching Docker Hub or GitOps.

This pipeline has been validated statically (unit tests parse every `platform-automate` command it runs and check its structure, see `automation/python/tests/unit/test_jenkins_automation_lab.py`) and the same lint commands run in GitHub Actions. It has not been run on a real Jenkins controller in this change.

### Stages

| Stage | Contacts | Fails the build when |
|---|---|---|
| Agent toolchain preflight | Nothing | `python3` or `git` missing, Python < 3.12, or `venv`/`ensurepip` missing (`MISSING REQUIRED TOOL`) |
| Python venv + install | PyPI | Install of `automation/python[dev]` fails |
| Ruff / Mypy / Unit tests (offline) | Nothing | Any lint error, type error or failing test |
| Ansible lint | Ansible Galaxy (collection download) | Collection install fails or any `ansible-lint` violation |
| Offline CLI checks | Nothing (`doctor` reads the local kubeconfig file only) | `doctor` crashes |
| Cluster dry-run (parameter `RUN_CLUSTER_DRY_RUN`) | `automation-lab` Kubernetes API, **read-only** | API unreachable, timed out, unauthorized, or plan/dry-run errors |
| Live lab (parameter `RUN_LIVE_LAB`) | `automation-lab` Kubernetes API, **writes** | Apply, wait, or verify fails |

Both parameters default to `false`. With both off, the build log ends with `Cluster-backed stages were SKIPPED ... no Kubernetes API was contacted.`, so a green build never implies that cluster checks ran. `RUN_LIVE_LAB` also runs the cluster dry-run first, and `--confirm` appears only in the live stage.

### Required checks and agent tools

Every check is required. There is no `|| true`, `catchError` or `returnStatus`, and every `sh` block starts with `set -eu`. Each lint and test command runs through `jenkins/scripts/run_check.py`, which prints and appends one line per check to `automation/reports/check-summary.txt` (archived and echoed in `post`):

| Status | Meaning | Build |
|---|---|---|
| `PASSED` | Command exited 0 | continues |
| `FAILED` | Non-zero exit or the per-check timeout expired | fails |
| `MISSING REQUIRED TOOL` | Executable not on `PATH`; the message names the install command | fails |
| `SKIPPED (optional tool not installed) ... did NOT run` | Only for checks declared `--optional` | continues, visibly |

No check is currently optional: `ruff`, `mypy`, `pytest`, `ansible-core` (for `ansible-galaxy`) and `ansible-lint` are pinned in the `dev` extra of `automation/python/pyproject.toml` and installed into the job's venv. The agent image only needs Python 3.12+ with `venv`, `pip` and `git` (see [Agent](#agent)); the pipeline does not upgrade any tool beyond those pins. `ansible-lint` runs from `automation/ansible` so `ansible.cfg` and `.ansible-lint` apply, after `ansible-galaxy` installs the pinned collections from `collections/requirements.yml`.

### Dry-run guarantees

- `kubernetes ensure --dry-run` and `platform plan` never create, update or delete anything, including when a read fails. They do **read** the Kubernetes API, so they are not offline.
- `kubernetes preflight` is a bounded `GET /version` plus a read of the `automation-lab` namespace.
- Every API call uses `--timeout` (stage value `KUBE_TIMEOUT_SECONDS=20`): connect ≤ 10 s, read ≤ 20 s, no urllib3 retries. The stage itself has a 5-minute Jenkins timeout as a backstop.
- An unreachable API exits 5 (`is unreachable`) or 6 (`did not respond within ...`) and fails the stage; it never hangs or passes.
- `platform verify` exits 4 when the demo pods are missing or not Ready.

Tests covering these guarantees run offline against a local fake API server (`automation/python/tests/unit/test_kubernetes_dry_run.py`).

### Cluster stage prerequisites

The agent needs a kubeconfig (`KUBECONFIG` or `~/.kube/config` for the `jenkins` user) whose current context, or `--context`, reaches the `ckad-lab` API, plus RBAC to read and, for the live stage, write in `automation-lab`. The agent image does not include one; provide it through a Jenkins credential, never through Git.

### Troubleshooting a connectivity timeout

1. Read the first error line: `did not respond within 10s connect / 20s read` means packets are dropped (VM stopped, VPN or route missing, wrong server IP). `is unreachable: NewConnectionError` (or `NameResolutionError`) means the connection was refused or the name did not resolve. `failed to load kubeconfig` means the agent has no kubeconfig or context.
2. From the agent container, repeat the read-only check: `platform-automate --timeout 10 kubernetes preflight` (add `--context <name>` if needed).
3. Confirm the server address in the kubeconfig is reachable from the Docker Desktop network, not just from the Windows host.
4. Re-run the job with `RUN_CLUSTER_DRY_RUN` only; leave `RUN_LIVE_LAB` off until preflight is `OK`.

More detail: [kubernetes-api-failure runbook](../docs/runbooks/kubernetes-api-failure.md#connectivity-timeouts).

## Next digest-pinned application release

After this hardening lands on `main`, the next application release should bump `APP_VERSION` under `app/` (for example to `0.1.5`), push an `app/**` commit, and let Jenkins publish the new tag, capture the digest, and promote both overlays. Do not bump the version until that release milestone starts. This milestone does not publish a new application version.
