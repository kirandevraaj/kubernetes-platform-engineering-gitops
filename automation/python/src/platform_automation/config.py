"""Configuration with defaults < YAML < env < CLI precedence."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import yaml

from platform_automation.errors import ConfigurationError

ALLOWED_ENVIRONMENTS = frozenset({"vmware", "aws"})
ALLOWED_CLUSTERS = frozenset({"ckad-lab", "platform-lab-aws"})
LAB_NAMESPACES = frozenset({"automation-lab", "security-lab", "argo-advanced-lab"})
DEFAULT_NAMESPACE = "automation-lab"


@dataclass
class Settings:
    environment: str = "vmware"
    cluster: str = "ckad-lab"
    namespace: str = DEFAULT_NAMESPACE
    region: str = "us-east-1"
    aws_profile: str | None = None
    context: str | None = None
    config_path: str | None = None
    dry_run: bool = False
    confirm: bool = False
    timeout: float = 120.0
    max_retries: int = 3
    verbose: bool = False
    quiet: bool = False
    report_dir: str = "automation/reports"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def kube_context(self) -> str:
        return self.context or self.cluster


_ENV_MAP = {
    "PLATFORM_ENVIRONMENT": ("environment", str),
    "PLATFORM_AUTOMATION_ENVIRONMENT": ("environment", str),
    "PLATFORM_CLUSTER": ("cluster", str),
    "PLATFORM_AUTOMATION_CLUSTER": ("cluster", str),
    "PLATFORM_NAMESPACE": ("namespace", str),
    "PLATFORM_AUTOMATION_NAMESPACE": ("namespace", str),
    "PLATFORM_REGION": ("region", str),
    "PLATFORM_AUTOMATION_REGION": ("region", str),
    "AWS_REGION": ("region", str),
    "AWS_DEFAULT_REGION": ("region", str),
    "PLATFORM_AWS_PROFILE": ("aws_profile", str),
    "AWS_PROFILE": ("aws_profile", str),
    "PLATFORM_CONTEXT": ("context", str),
    "PLATFORM_AUTOMATION_CONTEXT": ("context", str),
    "PLATFORM_DRY_RUN": ("dry_run", "bool"),
    "PLATFORM_CONFIRM": ("confirm", "bool"),
    "PLATFORM_TIMEOUT": ("timeout", float),
    "PLATFORM_AUTOMATION_TIMEOUT": ("timeout", float),
    "PLATFORM_MAX_RETRIES": ("max_retries", int),
    "PLATFORM_AUTOMATION_MAX_RETRIES": ("max_retries", int),
    "PLATFORM_VERBOSE": ("verbose", "bool"),
    "PLATFORM_QUIET": ("quiet", "bool"),
    "PLATFORM_AUTOMATION_CONFIG": ("config_path", str),
}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _coerce(value: Any, kind: Any) -> Any:
    if kind == "bool":
        if isinstance(value, bool):
            return value
        return _parse_bool(str(value))
    if kind is float:
        return float(value)
    if kind is int:
        return int(value)
    if value is None:
        return None
    return str(value)


def load_yaml_config(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise ConfigurationError(f"config file not found: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigurationError("config root must be a mapping")
    banned = {"password", "token", "secret", "aws_secret_access_key", "private_key"}
    for key in data:
        lowered = str(key).lower()
        if lowered in banned or "secret" in lowered:
            raise ConfigurationError(
                f"Refusing secret key {key!r} in YAML; use environment variables"
            )
    return data


def _apply_mapping(settings: Settings, data: dict[str, Any]) -> None:
    known = {f.name for f in fields(Settings)}
    for key, value in data.items():
        if key not in known or value is None:
            continue
        field = next(f for f in fields(Settings) if f.name == key)
        # Infer bool from default type
        if isinstance(field.default, bool):
            setattr(settings, key, _coerce(value, "bool"))
        elif isinstance(field.default, float):
            setattr(settings, key, float(value))
        elif isinstance(field.default, int):
            setattr(settings, key, int(value))
        else:
            setattr(settings, key, value)


def apply_env(settings: Settings, environ: dict[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    for env_key, (attr, kind) in _ENV_MAP.items():
        if env_key not in env:
            continue
        setattr(settings, attr, _coerce(env[env_key], kind))


def apply_cli_overrides(settings: Settings, overrides: dict[str, Any] | None) -> None:
    if not overrides:
        return
    cleaned = {k: v for k, v in overrides.items() if v is not None}
    _apply_mapping(settings, cleaned)


def load_settings(
    *,
    config_path: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> Settings:
    """Load settings with precedence: defaults < YAML < env < CLI."""
    settings = Settings()
    yaml_data = load_yaml_config(config_path)
    _apply_mapping(settings, yaml_data)
    apply_env(settings, environ)
    apply_cli_overrides(settings, cli_overrides)

    if settings.environment not in ALLOWED_ENVIRONMENTS:
        raise ConfigurationError(
            f"invalid environment: {settings.environment}; "
            f"allowed={sorted(ALLOWED_ENVIRONMENTS)}"
        )
    if settings.cluster not in ALLOWED_CLUSTERS:
        raise ConfigurationError(
            f"invalid cluster: {settings.cluster}; allowed={sorted(ALLOWED_CLUSTERS)}"
        )
    if settings.context is None:
        settings.context = settings.cluster
    return settings
