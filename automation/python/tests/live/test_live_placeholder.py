"""Live tests — skipped by default."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.live


def test_live_placeholder() -> None:
    """Placeholder: enable with pytest --live against a lab cluster/AWS profile."""
    pytest.skip("implement against live ckad-lab / platform-lab-aws when ready")
