# AWS / Terraform tooling container

Isolated Ubuntu LTS workstation for Step 10 (AWS + Terraform). Keeps cloud CLIs off the Windows host and out of the VMware Kubernetes nodes.

## Why this exists

| Concern | Approach |
|---|---|
| Host pollution | Do not install AWS CLI / Terraform on Windows |
| Credential safety | Never bake secrets into the image |
| Reproducibility | One Dockerfile builds a known Ubuntu toolbox |
| Project access | Bind-mount the Git repo at `/workspace` |

This container is for **tooling only**. Creating AWS infrastructure still requires an explicit later approval.

## Build

From the repository root:

```powershell
docker build -t platform-aws-tools:latest -f tools/aws/Dockerfile tools/aws
```

Or with Compose:

```powershell
docker compose -f tools/aws/compose.yaml build
```

Do not push this image to a registry for this lab.

## Start

```powershell
docker compose -f tools/aws/compose.yaml up -d
```

Equivalent run (if not using Compose):

```powershell
docker run -d --name platform-aws-tools `
  -v "${PWD}:/workspace" `
  -w /workspace `
  platform-aws-tools:latest `
  sleep infinity
```

## Enter the shell

```powershell
docker exec -it platform-aws-tools bash
```

Inside the container, the project root is `/workspace` (this Git repository).

## Workspace mapping

| Host | Container |
|---|---|
| Repository root (`kubernetes-platform-engineering-gitops/`) | `/workspace` |

Edits inside `/workspace` are edits on the host files.

## AWS authentication

Credentials must **never** go in the Dockerfile or Git.

`compose.yaml` mounts a Docker named volume `platform-aws-tools-aws` at `/root/.aws` so CLI config survives image rebuilds without baking secrets into layers.

Configure once inside the running container:

```powershell
docker exec -it platform-aws-tools bash
aws configure
# or: aws login / SSO as appropriate
```

Do not commit anything under `/root/.aws`.

## Remove and recreate

```powershell
docker compose -f tools/aws/compose.yaml down
docker compose -f tools/aws/compose.yaml build --no-cache
docker compose -f tools/aws/compose.yaml up -d
```

## Installed tools

| Tool | Notes |
|---|---|
| Ubuntu | 24.04 LTS (noble) |
| Architecture | linux/amd64 |
| AWS CLI | v2 (official installer) |
| Terraform | HashiCorp apt (current) |
| kubectl | **v1.36.x** from `dl.k8s.io` `stable-1.36` (compatible with EKS 1.36) |
| Helm | official `get-helm-3` |
| Git / curl / jq / unzip | apt |

Rebuild the image after Dockerfile changes and re-check `kubectl version --client`.

## Warnings

- **Never** store AWS credentials in the Dockerfile.
- **Never** commit AWS credentials, `*.tfvars` with secrets, or kubeconfigs.
- **Never** store Terraform state in Git (`.tfstate` is gitignored).
- Do **not** mount the Docker socket into this container unless a demonstrated need appears.
- Do **not** run `terraform apply` / `destroy` from this container until Step 10 explicitly authorizes it.
