# Role: platform_node

Read-only facts helper. Gathers minimal facts and may write a summary under `ansible_lab_workdir` on localhost via `delegate_to`.

## Interface

| Input | Default | Description |
|---|---|---|
| `platform_node_gather_subset` | `[min]` | `setup` gather_subset |
| `platform_node_write_facts` | `true` | Write local summary files |
| `platform_node_subdir` | `roles/platform_node` | Under `ansible_lab_workdir` |

## Outputs

- Optional `{{ inventory_hostname }}_facts.txt` on localhost workdir
- `READONLY.txt` notice

## Idempotency

Fact gathering is read-only. File writes use `template`/`copy` → stable on re-run.

## Safety

Intended for localhost or **read-only** use against optional VMware workers. Does not change remote packages, services, or kubelet. Never apply mutative tasks to cluster nodes from this role.
