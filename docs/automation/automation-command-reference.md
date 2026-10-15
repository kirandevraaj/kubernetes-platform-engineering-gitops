# Automation Command Reference (Project 1)

Safe, lab-oriented commands. Prefer dry-run/check modes first.  
**Mutate only** `automation-lab` (and documented lab exceptions). **Do not** mutate `platform-lab`, `storage-lab`, observability, VPC, EKS, ALB, Jenkins architecture, or Argo global objects.

Toolchain pins: [toolchain-inventory.md](../toolchain-inventory.md)

---

## Python / pip / pytest / ruff / mypy

```powershell
cd automation\python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -c "import kubernetes, boto3; print('ok')"
pytest -q
ruff check src tests
mypy src
```

CLI workflow (`--environment` is `vmware` or `aws`; global flags may go before or after the subcommand):

```powershell
platform-automate doctor
platform-automate --timeout 10 kubernetes preflight
platform-automate platform inventory --environment vmware
platform-automate platform plan
platform-automate kubernetes ensure --dry-run
# DANGEROUS without review — requires confirm; lab namespace only:
platform-automate platform reconcile --confirm --environment vmware
platform-automate platform verify
platform-automate report
```

`kubernetes ensure`, `kubernetes delete` and `platform apply`/`reconcile` refuse to mutate without `--confirm` (or run as a preview with `--dry-run`). `ansible --playbook ...` requires `--check` or `--confirm`.

**Dry-run is not offline.** What each command touches:

| Command | Kubernetes API | Writes |
|---------|----------------|--------|
| `doctor` | None (reads the local kubeconfig file only) | None |
| `kubernetes preflight` | `GET /version`, read namespace `automation-lab` | None |
| `platform plan` (with or without `--dry-run`) | List pods in `automation-lab` | None |
| `kubernetes ensure --dry-run` | Read ConfigMap, Deployment and Service to compute would-create / would-update | None, even when a read fails |
| `kubernetes ensure` without `--confirm` | None (refused before connecting, exit 3) | None |
| `kubernetes ensure --confirm` | Read, then create/patch in `automation-lab` | Yes |

Every API call is bounded by `--timeout` (connect ≤ 10 s, no retries). An unreachable API exits 5 or 6 with a message pointing at `kubernetes preflight`; it never hangs or exits 0. `platform plan` reports RBAC/HTTP errors in its output but exits non-zero on connectivity failures. See [kubernetes-api-failure](../runbooks/kubernetes-api-failure.md#connectivity-timeouts).

---

## kubectl (read-first)

Context examples: `ckad-lab`, AWS tools context.

```powershell
kubectl version --client
kubectl config get-contexts
kubectl config use-context ckad-lab
kubectl get ns
kubectl -n automation-lab get all
kubectl -n automation-lab get deploy,svc,pods -o wide
kubectl -n automation-lab describe deploy
kubectl -n automation-lab get events --sort-by=.lastTimestamp
```

**Destructive — do not run against production-like apps:**

```powershell
# WARNING: deletes resources. Never target platform-lab / storage-lab in this lab milestone.
kubectl -n automation-lab delete deploy <name>   # lab only, intentional cleanup
```

**Forbidden pattern:**

```powershell
# DO NOT — breaks GitOps boundary (Jenkins/human bypass of Argo for apps)
kubectl -n platform-lab apply -f ...
kubectl -n platform-lab set image deploy/platform-lab ...
```

---

## aws CLI

> **Note:** aws CLI may be **missing** from Windows PATH and WSL in the current workstation inventory. Install/configure before using. Prefer boto3 inside Python automation for logic.

```bash
aws sts get-caller-identity
aws eks describe-cluster --name <lab-cluster> --region ap-south-1
aws ec2 describe-instances --filters "Name=tag:Project,Values=platform-lab" --region ap-south-1
```

**Destructive (warn):**

```bash
# WARNING: can terminate capacity / break labs. Not part of Section 24 happy path.
aws ec2 terminate-instances --instance-ids i-...
aws eks delete-cluster --name ...
```

---

## terraform

> **Note:** terraform may be **not installed** on Windows PATH / WSL yet. Commands assume a future install. Always plan before apply.

```bash
cd terraform/aws
terraform fmt -check
terraform init
terraform validate
terraform plan -out=tfplan
# WARNING: mutates AWS. Gated human/CI approval only.
terraform apply tfplan
```

**Destructive:**

```bash
# WARNING: destroy removes infrastructure. Do not run casually.
terraform destroy
```

---

## ansible / ansible-playbook / galaxy / inventory / lint

From `automation/ansible` (when ansible-core available on PATH or via venv):

```bash
ansible --version
ansible-galaxy collection install -r collections/requirements.yml -p collections
ansible-inventory -i inventory/hosts.yml --list
ansible lab -i inventory/hosts.yml -m ansible.builtin.ping
ansible lab -i inventory/hosts.yml -m ansible.builtin.setup
ansible-playbook -i inventory/hosts.yml playbooks/lab_validate.yml --syntax-check
ansible-playbook -i inventory/hosts.yml playbooks/lab_validate.yml --check --diff
ansible-lint --offline playbooks   # uses .ansible-lint; needs the collections installed above
```

**Apply (lab localhost only):**

```bash
# Requires reviewed playbook; prefer Python Runner wrapper with --confirm
ansible-playbook -i inventory/hosts.yml playbooks/lab_baseline.yml
```

**Destructive / unsafe patterns:**

```bash
# WARNING: do not target vmware_workers for package install / reboot in this lab
ansible vmware_workers -m ansible.builtin.apt -a "name=... state=absent"
# WARNING: shell/command without guards breaks idempotency
ansible lab -m ansible.builtin.shell -a "rm -rf /..."
```

---

## git (safe)

```powershell
git status
git diff
git log -5 --oneline
```

Promotion commits for app digests are **Jenkins-owned**. Manual overlay digest edits risk fighting CI—coordinate deliberately.

---

## Exit code quick map

From `automation/python/src/platform_automation/errors.py`:

| Code | Meaning |
|------|---------|
| 0 | OK / verify PASS |
| 1 | Other automation error |
| 2 | Configuration (bad config file, invalid timeout) |
| 3 | Validation (namespace outside allow-list, missing `--confirm`) |
| 4 | Command failed / `platform verify` FAIL / Ansible rc ≠ 0 |
| 5 | API error, including Kubernetes API unreachable |
| 6 | Timeout (API did not respond, `kubernetes wait` not Ready) |
| 7 | Authentication/authorization (kubeconfig, 401/403, AWS credentials) |

---

## Related runbooks

- [automation-failure.md](../runbooks/automation-failure.md)  
- [python-automation.md](../runbooks/python-automation.md)  
- [ansible-failure.md](../runbooks/ansible-failure.md)  
- [aws-api-failure.md](../runbooks/aws-api-failure.md)  
- [kubernetes-api-failure.md](../runbooks/kubernetes-api-failure.md)  
