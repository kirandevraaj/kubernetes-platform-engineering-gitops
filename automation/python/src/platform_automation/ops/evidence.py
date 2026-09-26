"""Collect a local read-only incident evidence bundle with redaction."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from platform_automation.ops.redact import FORBIDDEN_EVIDENCE_COMMANDS, redact_text, scrub_mapping

Collector = Callable[[], str]


def _safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_text(content), encoding="utf-8")


def collect_evidence_bundle(
    *,
    output_dir: Path | str,
    context: str,
    collectors: dict[str, Collector] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write timestamped evidence files. Never runs secret-scraping collectors.

    ``collectors`` maps filename stem → zero-arg callable returning text.
    If a collector raises, the failure is recorded without stack secrets.
    """
    stamped = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(output_dir) / stamped
    root.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "mode": "read-only",
        "files": [],
        "errors": [],
        "forbidden_patterns": list(FORBIDDEN_EVIDENCE_COMMANDS),
        "metadata": scrub_mapping(metadata or {}),
    }

    default_collectors: dict[str, Collector] = {
        "cluster": lambda: f"context={context}\n",
        "README": lambda: (
            "Incident evidence bundle (READ-ONLY).\n"
            "Secrets, tokens, kubeconfigs, and AWS credentials are forbidden.\n"
        ),
    }
    active = {**default_collectors, **(collectors or {})}

    for name, fn in active.items():
        lower = name.lower()
        if any(bad in lower for bad in ("secret", "token", "kubeconfig", "credential")):
            manifest["errors"].append(
                {"file": name, "error": "collector name rejected (fail closed)"}
            )
            continue
        try:
            content = fn()
            if any(bad in content.lower() for bad in ("kind: secret", "data:\n  token:")):
                manifest["errors"].append(
                    {"file": name, "error": "content looked secret-like; skipped (fail closed)"}
                )
                continue
            filename = f"{name}.txt"
            _safe_write(root / filename, content)
            manifest["files"].append(filename)
        except Exception as exc:  # noqa: BLE001
            manifest["errors"].append({"file": name, "error": exc.__class__.__name__})

    _safe_write(root / "manifest.json", json.dumps(manifest, indent=2, default=str))
    return {"path": str(root), "manifest": manifest}
