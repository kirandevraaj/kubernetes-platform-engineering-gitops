"""Environment doctor — toolchain and connectivity checks."""

from __future__ import annotations

import shutil
from typing import Any

from platform_automation import __version__
from platform_automation.config import Settings


def run_doctor(settings: Settings) -> dict[str, Any]:
    tools = {
        "kubectl": shutil.which("kubectl"),
        "helm": shutil.which("helm"),
        "aws": shutil.which("aws"),
        "terraform": shutil.which("terraform"),
        "ansible-playbook": shutil.which("ansible-playbook"),
        "git": shutil.which("git"),
    }
    checks: list[dict[str, Any]] = []
    for name, path in tools.items():
        checks.append(
            {
                "name": name,
                "status": "OK" if path else "MISSING",
                "path": path,
            }
        )

    python_imports = {}
    for mod in ("kubernetes", "boto3", "yaml", "httpx"):
        try:
            __import__(mod)
            python_imports[mod] = "OK"
        except ImportError:
            python_imports[mod] = "MISSING"

    # ansible-runner may fail on Windows (fcntl)
    try:
        import ansible_runner  # noqa: F401

        python_imports["ansible_runner"] = "OK"
    except Exception as exc:  # noqa: BLE001
        python_imports["ansible_runner"] = f"UNAVAILABLE ({exc.__class__.__name__})"

    kube = {"status": "SKIPPED"}
    try:
        from platform_automation.kubernetes.client import get_current_context, list_context_names

        kube = {
            "status": "OK",
            "current_context": get_current_context(),
            "contexts": list_context_names(),
            "requested_context": settings.kube_context(),
        }
    except Exception as exc:  # noqa: BLE001
        kube = {"status": "ERROR", "error": str(exc)}

    return {
        "version": __version__,
        "settings": {
            "environment": settings.environment,
            "cluster": settings.cluster,
            "namespace": settings.namespace,
            "region": settings.region,
        },
        "tools": checks,
        "python_imports": python_imports,
        "kubernetes": kube,
        "notes": [
            "ansible-runner uses fcntl and is Linux-oriented; Windows uses ansible-playbook subprocess fallback",
            "mutations are limited to automation-lab",
            "aws CLI / terraform may be missing on Windows PATH — Boto3 and Terraform wrappers still teach the model",
        ],
    }
