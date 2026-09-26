# Postmortem: Argo ComparisonError (waves-health)

| Field | Value |
|---|---|
| Severity | SEV-3 (demo app Unknown) |
| Environment | Argo Application waves-health |

## Symptom
ComparisonError; Application Unknown; no desired manifests.

## Root cause
Kustomize failed to resolve `../base/namespace.yaml` (source generation problem).

## Detection
Argo Application conditions / ComparisonError message.

## Fix
Self-contained kustomization → manifests generated → Synced/Healthy.

## Lesson
ComparisonError often means **manifest generation**, not “cluster is down.” Fix the Git/kustomize source.
