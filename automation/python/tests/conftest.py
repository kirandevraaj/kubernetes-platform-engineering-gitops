"""Shared pytest configuration and markers."""

from __future__ import annotations

import pytest

_CLEARED_ENV = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "PLATFORM_CONFIRM",
    "PLATFORM_DRY_RUN",
    "PLATFORM_CONTEXT",
    "PLATFORM_AUTOMATION_CONTEXT",
    "PLATFORM_AUTOMATION_CONFIG",
)


@pytest.fixture(autouse=True)
def _offline_only(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Keep non-live tests away from the developer's kubeconfig, AWS profile and clusters."""
    if request.node.get_closest_marker("live"):
        return
    from kubernetes.config import kube_config

    missing_kubeconfig = tmp_path / "no-kubeconfig"
    # kubernetes reads KUBECONFIG once at import time; patch the resolved default too.
    monkeypatch.setattr(kube_config, "KUBE_CONFIG_DEFAULT_LOCATION", str(missing_kubeconfig))
    monkeypatch.setenv("KUBECONFIG", str(missing_kubeconfig))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-aws-config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-aws-credentials"))
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    for name in _CLEARED_ENV:
        monkeypatch.delenv(name, raising=False)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast offline unit tests with mocks")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "live: live cluster/AWS tests (skipped by default)")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live tests unless --live is passed or LIVE=1."""
    import os

    run_live = config.getoption("--live", default=False) or os.environ.get("LIVE") == "1"
    if run_live:
        return
    skip_live = pytest.mark.skip(reason="live tests skipped by default; pass --live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="run live AWS/Kubernetes tests",
    )
