# Runbook: AWS API Failure (Project 1)

**Scope:** Boto3 / aws CLI calls for inventory and rare tagged lab mutations.  
**Boundary:** VPC, EKS control plane, ALB are **Terraform-owned**—do not “fix” with ad-hoc deletes/creates.

---

## Symptoms

- `ClientError` / `AccessDenied` / `ExpiredToken` / `Throttling`  
- Empty inventory (wrong region/profile)  
- Pagination stopped early (partial list)  
- Doctor fails AWS section

---

## Checks

```bash
# If aws CLI installed:
aws sts get-caller-identity
aws configure list
echo %AWS_PROFILE% %AWS_REGION%   # PowerShell: $env:AWS_PROFILE
```

In Python venv:

```powershell
python -c "import boto3; print(boto3.__version__); boto3.Session().client('sts').get_caller_identity()"
```

---

## Common failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Wrong/missing profile | NoCreds / wrong account | Set `AWS_PROFILE` / shared config |
| Wrong region | ResourceNotFound / empty | Use `ap-south-1` (lab) or configured region |
| AccessDenied | Error Code AccessDenied | Fix IAM—**do not** broaden to Administrator for convenience without review |
| Throttling / 429 | ThrottlingException | Backoff; reduce forks; retry budget |
| Expired token | ExpiredToken | Re-auth SSO/session |
| Mutate blocked by policy | AccessDenied on write | Expected for read-mostly profile—do not escalate casually |
| CLI not on PATH | command not found | Use boto3; install CLI later per toolchain notes |

---

## Recovery

1. Fix identity/region first (`get-caller-identity`).  
2. Re-run read-only inventory.  
3. If throttled: wait, lower concurrency, re-run.  
4. Infra drift belonging to Terraform → `terraform plan` (not boto3 recreate).  
5. Never terminate random EC2 or delete EKS to clear errors.

---

## Evidence to capture

- AWS account id + ARN (not secret keys)  
- Region, API action, Error Code, RequestId  
- Whether call was read or mutate  

---

## Related

[automation-failure](./automation-failure.md) · [python-platform-automation](../automation/python-platform-automation.md)
