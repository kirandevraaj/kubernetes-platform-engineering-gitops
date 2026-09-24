# platform-lab

A small FastAPI service that will be the workload for the Kubernetes Platform Engineering and GitOps Lab. It has no database, authentication, or external dependencies. It can run on the workstation or in a local container. The image has not been pushed to Docker Hub.

## Purpose

Give the rest of the project one application to build, test, package, and deploy. The service identifies itself and exposes a health response that a future Kubernetes probe can call.

## Architecture

```text
app/
├── src/main.py           FastAPI application and HTTP routes
├── src/__init__.py       APP_VERSION, the only version constant
├── tests/                pytest API tests
├── requirements.txt      runtime dependencies used by the image
├── requirements-dev.txt  runtime dependencies plus the test tools
├── Dockerfile            local image build
└── .dockerignore
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
.\.venv\Scripts\python -m pip install -r app\requirements-dev.txt
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

## Docker

The image packages the runtime service only. Tests stay on the workstation. Build it locally as `kirandevraaj/platform-lab:0.1.0`. That name matches the Docker Hub repository, and this tag has not been pushed.

From the repository root:

```powershell
docker build -f app/Dockerfile -t kirandevraaj/platform-lab:0.1.0 app
```

Run it with port 8000 on the workstation mapped to port 8000 in the container:

```powershell
docker run --name platform-lab -d -p 8000:8000 kirandevraaj/platform-lab:0.1.0
```

Check the process and the health endpoint:

```powershell
docker inspect --format "{{.State.Health.Status}}" platform-lab
curl http://127.0.0.1:8000/health
```

`/health` returns `{"status":"healthy"}`. Docker also runs that endpoint from inside the container.

Stop and remove the container. This does not delete the local image:

```powershell
docker stop platform-lab
docker rm platform-lab
```

Inspect the local image:

```powershell
docker images kirandevraaj/platform-lab:0.1.0
docker inspect kirandevraaj/platform-lab:0.1.0
```
