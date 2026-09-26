# Terraform Plan Failure

## Symptoms
`terraform fmt/validate/plan` errors; unexpected diff; state lock; provider auth errors.

## First 60 Seconds (READ-ONLY / SAFE)
```bash
terraform fmt -check -recursive
terraform validate
terraform plan -out=tfplan-review   # REVIEW only — do not apply blindly
```

**Classification:** `plan` = READ-ONLY intent (may refresh state). Never treat refresh side effects casually in shared state.

## Diagnosis
Syntax; module source; variable missing; provider credentials (do not log secrets); state drift vs code.

## Safe Remediation
Fix code; re-plan; peer review saved plan. **Never** teach blind `terraform apply`.

## Do Not Do
`terraform destroy` as normal ops; commit `tfplan*` or state files; paste credentials.

## Related
[terraform-apply-safety.md](./terraform-apply-safety.md) · [terraform-infrastructure-recovery.md](./terraform-infrastructure-recovery.md)
