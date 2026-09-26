# Screenshot plan

| # | Shot | Show | Hide |
|---|---|---|---|
| 1 | Architecture SVG | Full diagram | n/a |
| 2 | Argo apps | Synced/Healthy columns | secrets |
| 3 | Jenkins green build | Stage names | credentials |
| 4 | Grafana dashboard | Panels | admin password |
| 5 | Nodes Ready | Both envs | kubeconfig paths with tokens |
| 6 | PVC/PV Bound | storage-lab | AWS account IDs if sensitive |
| 7 | ApplicationSet | Generated apps | tokens |
| 8 | `kubectl auth can-i` | yes/no | unrelated secrets |
| 9 | DR restore evidence | Timings docs | secret YAML |
| 10 | `platform-automate ops health` | PASS JSON | AWS keys |

Never capture: AWS keys, tokens, private keys, kubeconfig auth, Secret data.
