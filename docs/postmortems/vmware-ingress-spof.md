# Postmortem: VMware Ingress SPOF

| Field | Value |
|---|---|
| Severity | SEV-2 potential under worker loss |
| Environment | VMware ingress-nginx |

## Symptom
Ingress path tied to single replica on `worker-02` — worker failure impacted ingress.

## Root cause
Single replica = SPOF; insufficient topology/PDB initially.

## Detection
Worker failure experiments; traffic path analysis.

## Fix
2 replicas on different workers + PDB; re-tested worker failures.

## Lesson
Ingress HA is part of platform reliability — not just app replicas. Do not claim zero packet loss for every failure mode.
