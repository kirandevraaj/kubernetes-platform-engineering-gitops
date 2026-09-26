"""Integration tests (marked; local mocks only)."""

from __future__ import annotations

import pytest

from platform_automation.config import load_settings
from platform_automation.controller import PlatformController


pytestmark = pytest.mark.integration


def test_controller_without_adapters() -> None:
    settings = load_settings(environ={})
    ctl = PlatformController(settings=settings)
    assert ctl.validate()["ok"] is True
    plan = ctl.plan()
    assert plan["changes"]
