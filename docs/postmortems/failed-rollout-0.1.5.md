# Postmortem: Failed Rollout 0.1.5

| Field | Value |
|---|---|
| Severity | SEV-3 (old RS kept serving) |
| Environment | VMware / GitOps |

## Symptom
Controlled bad release `0.1.5` — new ReplicaSet not Ready.

## Root cause
Bad image/spec; rollout could not become Ready.

## Detection
Deployment progressing; RS inspection; external endpoint stayed healthy (old pods).

## Fix
Git rollback to exact `0.1.4` digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` → Argo reconciled → recovery.

## Lesson
Preferred model is **Git rollback → Argo**, not `kubectl rollout undo` as the durable path.
