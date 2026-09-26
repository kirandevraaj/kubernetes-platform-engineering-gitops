# Metrics Server Unavailable

Do **not** confuse with Prometheus.

## Symptoms
`kubectl top` fails; HPA `FailedGetResourceMetric`.

## First 60 Seconds (READ-ONLY)
```bash
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
kubectl get pods -n kube-system -l k8s-app=metrics-server
kubectl describe pod -n kube-system -l k8s-app=metrics-server
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
```

## Diagnosis
APIService Available? kubelet reachable? cert/flags issues on Metrics Server?

## Safe Remediation
Restore Metrics Server via approved GitOps/platform process. Avoid ad-hoc flag experiments on production nodes.

## Verification
`kubectl top nodes` works; HPA metrics populate.

## Related
[hpa-not-scaling.md](./hpa-not-scaling.md)
