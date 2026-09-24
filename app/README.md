# platform-lab

A small FastAPI service that will be the workload for the Kubernetes Platform Engineering and GitOps Lab. It has no database, authentication, or external dependencies. Later steps will containerize it and deploy it. This step only runs it on the workstation.

## Purpose

Give the rest of the project one application to build, test, package, and deploy. The service identifies itself and exposes a health response that a future Kubernetes probe can call.

## Architecture

```text
app/
├── src/main.py      FastAPI application and HTTP routes
├── src/__init__.py  APP_VERSION, the only version constant
├── tests/           pytest API tests
└── requirements.txt runtime and test dependencies
```

`src/main.py` reads `APP_VERSION` from `src/__init__.py`. The process environment variable `APP_ENVIRONMENT` selects the environment name. When it is unset, the value is `local`.

## Endpoints

| Method | Path | Status | Response |
|---|---|---|---|
| GET | `/` | 200 | Application name, description, version, and environment |
| GET | `/health` | 200 | `{"status": "healthy"}` |
| GET | `/version` | 200 | Application name and version |
| GET | `/info` | 200 | Name, description, version, environment, Python version, and framework |

## Local setup

From the repository root, create an isolated virtual environment and install the application dependencies into it:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r app\requirements.txt
```

Use that interpreter for tests and for the server. The virtual environment stays on the workstation and is listed in `.gitignore`.

## Run tests

```powershell
.\.venv\Scripts\python -m pytest app\tests
```

## Start the application

```powershell
.\.venv\Scripts\python -m uvicorn src.main:app --app-dir app --host 127.0.0.1 --port 8000
```

Stop it with Ctrl+C.

To label a run as something other than `local`:

```powershell
$env:APP_ENVIRONMENT = "lab"
.\.venv\Scripts\python -m uvicorn src.main:app --app-dir app --host 127.0.0.1 --port 8000
```

## Example requests

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
curl http://127.0.0.1:8000/info
```
