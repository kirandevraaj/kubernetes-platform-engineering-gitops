"""PlatformController — discover → validate → plan → apply → verify → report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from platform_automation.config import Settings
from platform_automation.errors import ValidationError
from platform_automation.kubernetes.idempotent import ensure_demo_stack
from platform_automation.observability import OperationRecord, format_human, new_operation, write_report
from platform_automation.validation import require_confirm, require_namespace


class K8sPort(Protocol):
    def list_nodes(self) -> list[dict[str, Any]]: ...
    def list_namespaces(self) -> list[str]: ...
    def list_pods(self, namespace: str) -> list[dict[str, Any]]: ...


class AwsPort(Protocol):
    def identity(self) -> dict[str, Any]: ...


@dataclass
class PlatformController:
    settings: Settings
    k8s: K8sPort | None = None
    aws: AwsPort | None = None
    last_record: OperationRecord | None = field(default=None, repr=False)

    def discover(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "environment": self.settings.environment,
            "cluster": self.settings.cluster,
            "namespace": self.settings.namespace,
            "context": self.settings.kube_context(),
        }
        if self.k8s is not None:
            data["nodes"] = self.k8s.list_nodes()
            data["namespaces"] = self.k8s.list_namespaces()
        if self.aws is not None and self.settings.environment == "aws":
            data["aws_identity"] = self.aws.identity()
        return data

    def validate(self) -> dict[str, Any]:
        require_namespace(self.settings.namespace, mutation=False)
        issues: list[str] = []
        if self.settings.namespace != "automation-lab":
            issues.append("reconcile/apply only target automation-lab")
        if self.k8s is None:
            issues.append("kubernetes adapter not configured")
        return {"ok": not issues or self.settings.namespace == "automation-lab", "issues": issues}

    def plan(self) -> dict[str, Any]:
        desired = {
            "namespace": "automation-lab",
            "resources": ["ConfigMap/automation-demo-config", "Deployment/automation-demo", "Service/automation-demo"],
        }
        actual: dict[str, Any] = {"pods": []}
        if self.k8s is not None:
            try:
                actual["pods"] = self.k8s.list_pods("automation-lab")
            except Exception as exc:  # noqa: BLE001 — plan should not crash on missing ns
                actual["error"] = str(exc)
        changes = ["ensure automation-lab demo stack (create or no-op)"]
        risks = ["mutations limited to automation-lab", "requires --confirm to apply"]
        return {"desired": desired, "actual": actual, "changes": changes, "risks": risks}

    def apply(self, *, confirm: bool | None = None, dry_run: bool | None = None) -> list[dict[str, Any]]:
        confirm = self.settings.confirm if confirm is None else confirm
        dry_run = self.settings.dry_run if dry_run is None else dry_run
        if not dry_run:
            require_confirm(confirm, "platform apply")
        if self.k8s is None:
            raise ValidationError("kubernetes adapter required for apply")
        # ensure_demo_stack expects KubernetesFacade — structural typing at runtime
        return ensure_demo_stack(self.k8s, dry_run=dry_run)  # type: ignore[arg-type]

    def verify(self) -> dict[str, Any]:
        if self.k8s is None:
            return {"status": "UNKNOWN", "reason": "no kubernetes adapter"}
        try:
            pods = self.k8s.list_pods("automation-lab")
        except Exception as exc:  # noqa: BLE001
            return {"status": "FAIL", "reason": str(exc)}
        demo_pods = [p for p in pods if str(p.get("name", "")).startswith("automation-demo")]
        if not demo_pods:
            return {"status": "FAIL", "reason": "no automation-demo pods", "pods": pods}
        if all(p.get("ready") for p in demo_pods):
            return {"status": "PASS", "pods": demo_pods}
        return {"status": "FAIL", "reason": "pods not ready", "pods": demo_pods}

    def check(self) -> dict[str, Any]:
        """Drift detection without mutation."""
        plan = self.plan()
        verify = self.verify()
        if verify.get("status") == "PASS":
            compliance = "COMPLIANT"
        elif verify.get("status") == "FAIL":
            compliance = "DRIFTED"
        else:
            compliance = "UNKNOWN"
        return {"compliance": compliance, "plan": plan, "verify": verify}

    def report(self, record: OperationRecord | None = None) -> dict[str, Any]:
        rec = record or self.last_record
        if rec is None:
            rec = new_operation("report", self.settings.cluster, "summary", environment=self.settings.environment)
            rec.finish("OK")
        path = write_report(rec, self.settings.report_dir)
        return {"path": str(path), "human": format_human(rec), "json": rec.to_dict()}

    def reconcile(self) -> dict[str, Any]:
        record = new_operation(
            "reconcile",
            self.settings.cluster,
            "ensure-demo-stack",
            environment=self.settings.environment,
        )
        self.last_record = record
        discovery = self.discover()
        validation = self.validate()
        plan = self.plan()
        apply_result = self.apply()
        verify = self.verify()
        record.changes = [str(item.get("action")) for item in apply_result]
        record.verification = str(verify.get("status"))
        status = "OK" if verify.get("status") == "PASS" or self.settings.dry_run else "DEGRADED"
        record.finish(status)
        report = self.report(record)
        return {
            "discovery": discovery,
            "validation": validation,
            "plan": plan,
            "apply": apply_result,
            "verify": verify,
            "report": report,
        }
