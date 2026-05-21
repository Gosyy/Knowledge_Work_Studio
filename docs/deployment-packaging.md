# P6 Deployment packaging

P6 adds container packaging files for a deployable KW Studio stack.

## Files

```text
Dockerfile.backend
frontend/Dockerfile
docker-compose.deploy.yml
.env.deploy.example
.dockerignore
frontend/.dockerignore
scripts/kw_validate_deployment_package.py
```

## Deployment shape

The packaging defines three services:

```text
postgres  -> metadata database
backend   -> FastAPI API and artifact services
frontend  -> Next.js standalone runtime
```

The backend image copies both `backend/` and `skills/`. Runtime services import reusable skill packages such as `skills.docx`, so the container smoke gate must fail if the skill package is omitted from the image.

Persistent data is stored in named Docker volumes:

```text
postgres_data
kw_storage
```

For the backend container, local file storage is explicitly configured as `STORAGE_ROOT=/app/storage`, `UPLOADS_DIR=/app/storage/uploads`, `ARTIFACTS_DIR=/app/storage/artifacts`, and `TEMP_DIR=/app/storage/temp`. These paths must stay aligned with the `kw_storage:/app/storage` Docker volume so the non-root backend process can create upload, artifact, and temp files.

## First-time setup

Create a deployment environment file:

```bash
cp .env.deploy.example .env.deploy
```

Edit every `CHANGE_ME` value before starting the stack.

Minimum required values:

```text
POSTGRES_PASSWORD
DATABASE_URL
SECRET_KEY
```

The compose file intentionally requires `DATABASE_URL` and `SECRET_KEY` instead of silently inventing production secrets.

## Validate packaging

This validation does not require Docker:

```bash
python3 scripts/kw_validate_deployment_package.py --repo-root .
```

or:

```bash
make deploy-package-validate
```

## Build and run

Requires Docker Compose v2:

```bash
docker compose -f docker-compose.deploy.yml build
docker compose -f docker-compose.deploy.yml up -d
```

Makefile shortcuts:

```bash
make docker-build
make docker-up
make docker-down
```

## Smoke checks

After the stack is up:

```bash
python3 scripts/kw_operator_smoke.py --base-url http://localhost:8000 --frontend-url http://localhost:3000
```

## Scope boundaries

P6 does not add cloud deployment, Kubernetes, TLS termination, external object storage, or production auth. Those stay as explicit later-phase work.
