# Role: platform_common

Small baseline role for the Section 24 lab. Writes disposable markers under `ansible_lab_workdir` only.

## Interface

| Input | Default | Description |
|---|---|---|
| `platform_common_owner` | `platform-common` | Owner string in marker template |
| `platform_common_marker` | `platform_common_ok` | Marker token |
| `platform_common_subdir` | `roles/platform_common` | Path under `ansible_lab_workdir` |
| `ansible_lab_workdir` | from group_vars | Required disposable root |

## Outputs

- `{{ ansible_lab_workdir }}/roles/platform_common/marker.conf`
- `NOTICE.txt` copy
- `handler.stamp` when template changes

## Idempotency

Uses `file`, `template`, and `copy` modules. Second run → `changed=0` when inputs unchanged. Handler fires only on template change.

## Safety

Never targets `platform-lab`, workers, AWS infra, or cluster namespaces.
