#!/bin/bash
set -euo pipefail
kubectl config use-context platform-lab-aws >/dev/null
kubectl apply -f /workspace/gitops/projects/platform-storage-aws.yaml
kubectl -n argocd annotate application platform-storage-aws argocd.argoproj.io/refresh=hard --overwrite
# Free one slot for grafana pending: delete pending grafana pod; scale snapshot stays 1
kubectl -n observability delete pod -l app.kubernetes.io/name=grafana --field-selector=status.phase=Pending --ignore-not-found || true
# If still progressing, delete extra grafana replica set pending
sleep 5
for i in $(seq 1 24); do
  kubectl get application -n argocd -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status
  ST=$(kubectl get application -n argocd platform-storage-aws -o jsonpath='{.status.sync.status}')
  OH=$(kubectl get application -n argocd platform-observability-aws -o jsonpath='{.status.health.status}')
  echo "storage=$ST obs=$OH"
  if [ "$ST" = "Synced" ] && [ "$OH" = "Healthy" ]; then
    break
  fi
  # nudge sync
  if [ "$ST" != "Synced" ]; then
    kubectl -n argocd patch application platform-storage-aws --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}' 2>/dev/null || true
  fi
  sleep 10
done
kubectl get pods -n observability
kubectl get pods -n storage-lab
kubectl get application -n argocd
