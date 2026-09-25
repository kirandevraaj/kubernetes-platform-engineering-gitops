#!/usr/bin/env bash
# Destroy-safety helper for terraform/aws.
# Runs while the EKS API is still reachable (before Helm/EKS are destroyed).
# Goal: remove Ingress finalizers / Argo Applications so AWS ALBs and related
# security groups are deleted by the AWS Load Balancer Controller before the
# cluster disappears.
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:?CLUSTER_NAME is required}"
AWS_REGION="${AWS_REGION:?AWS_REGION is required}"
ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}"
APP_NAMESPACE="${APP_NAMESPACE:-platform-lab}"

echo "[pre-destroy] updating kubeconfig for ${CLUSTER_NAME} (${AWS_REGION})"
aws eks update-kubeconfig --name "${CLUSTER_NAME}" --region "${AWS_REGION}" >/dev/null

echo "[pre-destroy] deleting Argo CD Applications (triggers prune + Ingress removal)"
kubectl -n "${ARGOCD_NAMESPACE}" delete applications.argoproj.io --all --wait=true --timeout=10m || true

echo "[pre-destroy] deleting remaining Ingress objects cluster-wide"
kubectl delete ingress --all --all-namespaces --wait=true --timeout=10m || true

echo "[pre-destroy] waiting for AWS Load Balancer Controller to release ALBs (best-effort)"
# Poll for ALBs tagged by the cluster; tolerate already-deleted cluster later.
for _ in $(seq 1 60); do
  COUNT="$(aws elbv2 describe-load-balancers --region "${AWS_REGION}" \
    --query "length(LoadBalancers[?contains(LoadBalancerName, 'k8s-')])" \
    --output text 2>/dev/null || echo 0)"
  if [[ "${COUNT}" == "0" || "${COUNT}" == "None" ]]; then
    echo "[pre-destroy] no k8s-* ALBs remaining (or none visible)"
    break
  fi
  echo "[pre-destroy] still seeing ${COUNT} k8s-* ALB(s); sleeping 15s"
  sleep 15
done

echo "[pre-destroy] cleanup helper finished"
