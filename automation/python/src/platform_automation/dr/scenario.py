"""Disaster recovery scenario helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DrScenario:
    """Describes a DR exercise without hardcoding timestamps."""

    name: str
    failure_domain: str
    recovery_source: str
    recovery_mechanism: str
    tested: str = "documented_only"
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LAB_SCENARIOS: tuple[DrScenario, ...] = (
    DrScenario(
        name="git_desired_state_corruption",
        failure_domain="configuration",
        recovery_source="git",
        recovery_mechanism="git_revert_plus_argo_reconcile",
        tested="tested",
    ),
    DrScenario(
        name="argo_application_deleted",
        failure_domain="gitops_control",
        recovery_source="git",
        recovery_mechanism="recreate_application_from_git",
        tested="tested",
    ),
    DrScenario(
        name="namespace_deleted",
        failure_domain="kubernetes_namespace",
        recovery_source="git",
        recovery_mechanism="argo_create_namespace_reconcile",
        tested="tested",
    ),
    DrScenario(
        name="ebs_snapshot_restore",
        failure_domain="persistent_data",
        recovery_source="ebs_snapshot_via_csi",
        recovery_mechanism="volumesnapshot_to_new_pvc",
        tested="tested",
    ),
    DrScenario(
        name="worker_node_failure",
        failure_domain="compute",
        recovery_source="eks_nodegroup_scheduler",
        recovery_mechanism="node_replacement_reattach",
        tested="partially_tested",
        notes="Measured in prior storage resilience milestone (~6.3 minutes).",
    ),
    DrScenario(
        name="eks_cluster_unavailable",
        failure_domain="infrastructure",
        recovery_source="terraform_plus_git_plus_snapshots",
        recovery_mechanism="rebuild_then_restore_then_reconcile",
        tested="documented_only",
        notes="Not safe to destroy the main lab cluster.",
    ),
    DrScenario(
        name="aws_region_failure",
        failure_domain="region",
        recovery_source="cross_region_architecture",
        recovery_mechanism="multi_region_rebuild",
        tested="not_safe_to_test",
    ),
)


def get_scenario(name: str) -> DrScenario:
    for scenario in LAB_SCENARIOS:
        if scenario.name == name:
            return scenario
    raise KeyError(f"unknown DR scenario: {name}")


def list_scenarios() -> list[dict[str, Any]]:
    return [s.to_dict() for s in LAB_SCENARIOS]
