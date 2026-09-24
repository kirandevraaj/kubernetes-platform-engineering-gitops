"""API tests for the platform-lab workload."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi.testclient import TestClient

from src import APP_VERSION
from src.main import APP_DESCRIPTION, APP_NAME, APP_RELEASE, app

client = TestClient(app)


def test_root_returns_application_identity() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == APP_NAME
    assert body["description"] == APP_DESCRIPTION
    assert body["version"] == APP_VERSION
    assert body["version"] == "0.1.2"
    assert body["environment"] == "local"
    assert body["release"] == APP_RELEASE
    assert body["release"] == "automated-ci-cd"


def test_health_returns_healthy() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_version_returns_application_version() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"name": APP_NAME, "version": APP_VERSION}
    assert response.json()["version"] == "0.1.2"


def test_info_returns_non_sensitive_metadata() -> None:
    response = client.get("/info")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == APP_NAME
    assert body["description"] == APP_DESCRIPTION
    assert body["version"] == APP_VERSION
    assert body["environment"] == "local"
    assert body["framework"] == "fastapi"
    assert body["python"]
