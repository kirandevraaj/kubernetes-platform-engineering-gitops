"""Operation observability — structured results without credentials."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OperationRecord:
    operation_id: str
    operation: str
    target: str
    action: str
    status: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    environment: str = ""
    changes: list[str] = field(default_factory=list)
    verification: str = ""
    error_category: str = ""
    errors: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str, *, error_category: str = "", error: str | None = None) -> None:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error_category = error_category
        if error:
            self.errors.append(error)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Never persist credential-like extras
        banned = {"token", "password", "secret", "kubeconfig", "aws_secret_access_key"}
        extras = {
            k: v
            for k, v in data.get("extras", {}).items()
            if k.lower() not in banned and "secret" not in k.lower()
        }
        data["extras"] = extras
        return data


def new_operation(operation: str, target: str, action: str, *, environment: str = "") -> OperationRecord:
    return OperationRecord(
        operation_id=str(uuid.uuid4()),
        operation=operation,
        target=target,
        action=action,
        status="RUNNING",
        start_time=time.time(),
        environment=environment,
    )


def write_report(record: OperationRecord, report_dir: str) -> Path:
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{record.operation_id}.json"
    out.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    return out


def format_human(record: OperationRecord) -> str:
    lines = [
        f"operation_id: {record.operation_id}",
        f"environment:  {record.environment}",
        f"operation:    {record.operation}",
        f"target:       {record.target}",
        f"action:       {record.action}",
        f"status:       {record.status}",
        f"duration:     {record.duration:.3f}s" if record.duration is not None else "duration:     -",
        f"verification: {record.verification or '-'}",
        f"changes:      {', '.join(record.changes) if record.changes else 'none'}",
    ]
    if record.errors:
        lines.append(f"errors:       {'; '.join(record.errors)}")
    if record.error_category:
        lines.append(f"error_category: {record.error_category}")
    return "\n".join(lines)
