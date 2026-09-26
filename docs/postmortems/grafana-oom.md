# Postmortem: Grafana OOM (VMware)

| Field | Value |
|---|---|
| Severity | SEV-3 (observability impaired) |
| Environment | VMware `ckad-lab` / `monitoring` |

## Symptom
Grafana Pod OOMKilled / unstable UI.

## Root cause
Memory limit too low for workload.

## Detection
Pod restarts / OOM events; Argo health degraded.

## Fix
GitOps resource (memory) increase → Grafana stabilized.

## Lesson
Observability components need realistic requests/limits; fix via Git not one-off kubectl edit.
