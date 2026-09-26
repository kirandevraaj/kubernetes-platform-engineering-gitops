# Postmortem: VMware Worker Failure

| Field | Value |
|---|---|
| Severity | SEV-2 capacity / scheduling |
| Environment | VMware workers |

## Symptom
Kubelet stopped → Node NotReady → NoSchedule/NoExecute → application capacity reduced.

## Root cause
Worker/kubelet unavailable (lab fault injection).

## Detection
Node conditions; pod evictions; reduced Ready replicas.

## Fix
Kubelet restart → node Ready → workloads recover.

## Lesson
Node failure ≠ pod-only failure; distinguish from AWS EBS AZ-bound recovery (~6.3 min observed on AWS worker terminate).
