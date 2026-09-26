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
pip install -r requirements.txt
python -c "import kubernetes, boto3, ansible_runner; print('ok')"
pytest -q
ruff check .
ruff format --check .
mypy platform_automate
```

Doctor-style (once CLI exists):

```powershell
platform-automate doctor
platform-automate inventory --environment lab
platform-automate plan --dry-run
# DANGEROUS without review — requires confirm; lab namespace only:
platform-automate reconcile --confirm --environment lab
platform-automate verify
platform-automate report
```

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
ansible-lint
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

| Code | Meaning |
|------|---------|
| 0 | OK / verify PASS |
| 2 | Config/CLI validation |
| 3 | Auth/RBAC/IAM |
| 4 | Verify FAIL |
| 5 | Partial failure |
| 124 | Timeout |

---

## Related runbooks

- [automation-failure.md](../runbooks/automation-failure.md)  
- [python-automation.md](../runbooks/python-automation.md)  
- [ansible-failure.md](../runbooks/ansible-failure.md)  
- [aws-api-failure.md](../runbooks/aws-api-failure.md)  
- [kubernetes-api-failure.md](../runbooks/kubernetes-api-failure.md)  
