"""FastAPI application used as the project workload."""

import os
import sys
from typing import Literal

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from src import APP_VERSION

APP_NAME = "platform-lab"
APP_DESCRIPTION = (
    "Sample workload for the Kubernetes Platform Engineering and GitOps Lab."
)
APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "local")
APP_RELEASE = "automated-ci-cd"

app = FastAPI(title=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION)

# Expose Prometheus metrics at /metrics without changing application endpoints.
Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


class ApplicationResponse(BaseModel):
    name: str
    description: str
    version: str
    environment: str
    release: str


class HealthResponse(BaseModel):
    status: Literal["healthy"]


class VersionResponse(BaseModel):
    name: str
    version: str


class InfoResponse(BaseModel):
    name: str
    description: str
    version: str
    environment: str
    python: str
    framework: str


@app.get("/", response_model=ApplicationResponse, status_code=200)
def read_root() -> ApplicationResponse:
    return ApplicationResponse(
        name=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        environment=APP_ENVIRONMENT,
        release=APP_RELEASE,
    )


@app.get("/health", response_model=HealthResponse, status_code=200)
def health() -> HealthResponse:
    # Intentional 0.1.5 readiness-failure lab: break /health only on VMware
    # (APP_ENVIRONMENT=local-gitops). AWS overlay uses aws-eks-gitops and stays Ready.
    if APP_ENVIRONMENT == "local-gitops":
        raise HTTPException(
            status_code=503,
            detail="intentional readiness failure (0.1.5 lab)",
        )
    return HealthResponse(status="healthy")


@app.get("/version", response_model=VersionResponse, status_code=200)
def version() -> VersionResponse:
    return VersionResponse(name=APP_NAME, version=APP_VERSION)


@app.get("/info", response_model=InfoResponse, status_code=200)
def info() -> InfoResponse:
    return InfoResponse(
        name=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        environment=APP_ENVIRONMENT,
        python=sys.version.split()[0],
        framework="fastapi",
    )
