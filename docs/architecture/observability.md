# Observability architecture

Status: local lab observability for `platform-lab` using Prometheus and Grafana, managed through Argo CD.

## Request and scrape flow

```text
LAN / browser
     |
     +-- Host platform-lab.local ---------------------> ingress-nginx
     |                                                  (MetalLB VIP 192.168.56.200)
     |                                                           |
     |                                                           v
     |                                                  platform-lab ClusterIP :8000
     |                                                           |
     |                                                           | /metrics
     |                                                           v
     |                                                  Prometheus (ClusterIP)
     |                                                           ^
     |                                                           |
     +-- http://<grafana-EXTERNAL-IP>/  <-------------- Grafana (LoadBalancer)
                MetalLB allocates from lab-pool                 |
                (not the ingress VIP)                           |
                                                                +-- queries Prometheus
```

| Path | Component | Notes |
|---|---|---|
| Application HTTP | ingress-nginx → ClusterIP Service `platform-lab` | Unchanged; VIP remains `192.168.56.200` |
| Application metrics | Prometheus scrapes `/metrics` via ServiceMonitor | In-cluster only |
| Grafana UI | Dedicated LoadBalancer Service | MetalLB picks an unused address from `lab-pool`; discover with `kubectl get svc` |

Prometheus is not exposed on the LAN. Grafana is. There is no Grafana Ingress.

## Roles

| Component | Role |
|---|---|
| **Prometheus** | Time-series store and scraper. Discovers `platform-lab` through a ServiceMonitor and also scrapes kube-state-metrics / node-exporter from kube-prometheus-stack. |
| **Grafana** | Visualization. Provisioned dashboard ConfigMap `platform-lab-grafana-dashboard` (label `grafana_dashboard=1`). |
| **ServiceMonitor** | Declares scrape of Service `platform-lab`, port `http`, path `/metrics`, interval 30s. Lives in namespace `platform-lab` (local overlay). |
| **NetworkPolicy (local)** | Extends base policy so pods in namespace `monitoring` may reach TCP/8000 for scrapes. AWS overlay is unchanged. |

## Application metrics

FastAPI uses `prometheus-fastapi-instrumentator`. Endpoint `GET /metrics` returns Prometheus text. Existing routes (`/`, `/health`, `/version`, `/info`) are unchanged. Series include `http_requests_total` and `http_request_duration_seconds_*`.

## GitOps ownership

| Object | Owner |
|---|---|
| kube-prometheus-stack Helm release + Grafana dashboard ConfigMap | Argo CD Application `platform-lab-observability` |
| ServiceMonitor + NetworkPolicy scrape allow | Argo CD Application `platform-lab-local` (local overlay) |
| Image tag / app Deployment | `platform-lab-local` via Jenkins promotion of `newTag` only |

Chart: `kube-prometheus-stack` `91.5.1` from `https://prometheus-community.github.io/helm-charts`. Values: `observability/values-kube-prometheus-stack.yaml`.

## Validation commands

```powershell
kubectl config current-context   # ckad-lab

# Stack health
kubectl --context=ckad-lab get application -n argocd platform-lab-observability
kubectl --context=ckad-lab get pods,svc -n monitoring
kubectl --context=ckad-lab get svc -n monitoring -l app.kubernetes.io/name=grafana -o wide

# Application scrape path
kubectl --context=ckad-lab get servicemonitor -n platform-lab
kubectl --context=ckad-lab exec -n platform-lab deploy/platform-lab -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics', timeout=2).read()[:200])"

# Existing app / ingress regressions
curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/
curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/metrics
```

Grafana EXTERNAL-IP is assigned by MetalLB after sync. Do not hard-code it. Admin password is in Secret `kube-prometheus-stack-grafana` (base64 `admin-password`).

## Observed validation (24 September 2026)

| Check | Result |
|---|---|
| Application version | `0.1.3` via `http://platform-lab.local/` |
| Image | `kirandevraaj/platform-lab:0.1.3` digest `sha256:b2c2d0d5617c05e2fb36ab186e6ebd8bbd1de7c10a928ade922337f7df18f6ba` |
| Jenkins | Build `#12` SUCCESS (build/push/promote); build `#13` SUCCESS (loop prevention, no app rebuild) |
| Commits | `1c562fc` (implementation); `75cda8e` (Jenkins GitOps promote) |
| Argo CD | `platform-lab-local` Synced/Healthy; `platform-lab-observability` Synced/Healthy |
| Ingress VIP | `192.168.56.200` unchanged |
| Grafana EXTERNAL-IP | MetalLB assigned `192.168.56.201` (discovered; not reserved in Git) |
| Grafana UI | `http://192.168.56.201/login` HTTP 200; dashboard uid `platform-lab` (8 panels) loaded |
| Prometheus Service | ClusterIP only |
| ServiceMonitor targets | `job=platform-lab` **up** for both pods |
| Prometheus queries | `http_requests_total`, replica, CPU, and memory series returned data |

## Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| ServiceMonitor not created | Prometheus Operator CRDs not ready yet | `kubectl get crd servicemonitors.monitoring.coreos.com`; wait for `platform-lab-observability` Healthy |
| Target down in Prometheus | NetworkPolicy blocks scrape, or pods not Ready | Confirm local NetworkPolicy allows namespace `monitoring`; `kubectl get endpoints -n platform-lab` |
| Empty Grafana panels | Image still pre-`/metrics`, or no traffic | Confirm image tag ≥ `0.1.3`; generate traffic to `/` and `/health` |
| Grafana has no EXTERNAL-IP | MetalLB pool exhausted or Service not LoadBalancer | `kubectl get svc -n monitoring`; `kubectl get ipaddresspool -n metallb-system` |
| Ingress VIP changed | Grafana must not reuse `192.168.56.200` | Grafana Service is a separate LoadBalancer; ingress VIP should stay `.200` |
