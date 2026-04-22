# KW Studio offline intranet deployment profile

## Approved L3/M5 deployment model

KW Studio is hardened for this deployment profile:

- offline intranet application server
- remote Postgres as the single metadata truth layer
- storage backend as the binary truth layer
- GigaChat as the only active LLM provider
- access over LAN/VPN/bastion
- no hidden SQLite or fake-provider runtime fallback

## Required environment

```bash
DEPLOYMENT_MODE=offline_intranet
APP_ENV=production

METADATA_BACKEND=postgres
SQLITE_RUNTIME_ALLOWED=false
DATABASE_URL=postgresql+psycopg://kw_studio:<password>@postgres.internal:5432/kw_studio

# Local binary storage on approved internal disk/NAS/mounted remote volume
STORAGE_BACKEND=local
STORAGE_ROOT=/srv/kw_studio/storage
UPLOADS_DIR=/srv/kw_studio/storage/uploads
ARTIFACTS_DIR=/srv/kw_studio/storage/artifacts
TEMP_DIR=/srv/kw_studio/storage/temp

LLM_PROVIDER=gigachat
GIGACHAT_API_BASE_URL=https://gigachat-gateway.internal.example/api/v1
GIGACHAT_AUTH_URL=https://gigachat-gateway.internal.example/oauth
GIGACHAT_CLIENT_ID=<from secret store>
GIGACHAT_CLIENT_SECRET=<from secret store>

SECRET_KEY=<from secret store>
```

## MinIO / S3-compatible object storage

M5 wires a real S3-compatible object-storage adapter for MinIO, S3, or the
generic `remote_object_storage` alias.

Example internal MinIO profile:

```bash
STORAGE_BACKEND=minio
STORAGE_ENDPOINT=https://minio.internal.example:9000
STORAGE_BUCKET=kw-studio
STORAGE_ACCESS_KEY=<from secret store>
STORAGE_SECRET_KEY=<from secret store>
STORAGE_REGION=us-east-1
STORAGE_VERIFY_TLS=true
STORAGE_ADDRESSING_STYLE=path
```

`STORAGE_ADDRESSING_STYLE=path` is the default because it is a safe internal
default for MinIO/S3-compatible deployments. No silent fallback to local storage
occurs when a remote object-storage backend is selected.

## Health and readiness

- `/health` returns a simple process health response.
- `/ready` validates the deployment profile:
  - offline intranet mode
  - Postgres metadata truth layer
  - SQLite disabled for runtime
  - storage configuration present
  - supported addressing style
  - GigaChat-only provider
  - GigaChat URLs and credentials configured
  - non-default secret key configured

A non-ready profile returns HTTP 503 with explicit errors.
