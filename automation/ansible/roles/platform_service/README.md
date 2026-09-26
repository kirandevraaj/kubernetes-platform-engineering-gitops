# Role: platform_service

Simulates a small service configuration on disposable localhost paths. Does not start OS services or touch Kubernetes.

## Interface

| Input | Default | Description |
|---|---|---|
| `platform_service_name` | `platform-service` | Logical service name |
| `platform_service_port` | `18080` | Port recorded in config |
| `platform_service_enabled` | `true` | Skip tasks when false |
| `platform_service_subdir` | `roles/platform_service` | Under `ansible_lab_workdir` |

## Outputs

- `service.conf` (templated)
- `banner.txt`
- `reloaded.flag` when template changes (handler)

## Idempotency

Module-based `template`/`copy`/`file`. Unchanged inputs → `changed=0`; handler skipped.

## Safety

Localhost markers only. No systemd, kubelet, or cloud mutations.
