# Python Automation Failure (`platform-automate`)

## First diagnostic
```bash
platform-automate doctor
platform-automate verify
```

## Ops (READ-ONLY)
```bash
platform-automate ops health
platform-automate ops triage --symptom "pods pending"
platform-automate ops report
platform-automate ops evidence
```

## Symptoms
Non-zero exit; config/CLI errors; Kubernetes/AWS API failures; timeouts; bad structured report.

## Diagnosis
1. Doctor: tools/context/config  
2. Environment flags / kube context mixup (VMware vs AWS)  
3. Retry/timeout settings  
4. Redaction: evidence collectors must fail closed on unsafe output  

## Safe Remediation
Fix config/code; re-run unit tests; do not add mutation flags to ops commands.

## Verification
Doctor OK; unit tests pass; ops health matches kubectl READ-ONLY view.

## Related
[ansible-failure.md](./ansible-failure.md) · automation docs under `docs/automation/`
