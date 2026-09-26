"""Shared pytest configuration and markers."""

from __future__ import annotations

import pytest


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
