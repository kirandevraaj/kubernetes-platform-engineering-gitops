"""Secret-safe redaction for operational evidence."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_RE = re.compile(
    r"(password|secret|token|credential|authorization|private[_-]?key|"
    r"access[_-]?key|kubeconfig|api[_-]?key|bearer)",
    re.IGNORECASE,
)

SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9\-._~+/]+=*|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def redact_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if SENSITIVE_KEY_RE.search(line) and (":" in line or "=" in line):
            # Keep key name, scrub value-ish portion
            if ":" in line:
                key, _, _rest = line.partition(":")
                lines.append(f"{key}: [redacted]")
            elif "=" in line:
                key, _, _rest = line.partition("=")
                lines.append(f"{key}=[redacted]")
            else:
                lines.append("[redacted]")
            continue
        lines.append(SENSITIVE_VALUE_RE.sub("[redacted]", line))
    return "\n".join(lines)


def scrub_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                out[key] = "[redacted]"
            else:
                out[key] = scrub_mapping(item)
        return out
    if isinstance(value, list):
        return [scrub_mapping(v) for v in value]
    if isinstance(value, str):
        return redact_text(value) if SENSITIVE_VALUE_RE.search(value) else value
    return value


FORBIDDEN_EVIDENCE_COMMANDS = (
    "get secret",
    "get secrets",
    "describe secret",
    "kubectl get secret",
    "aws configure get",
    "cat kubeconfig",
)
