# KW Studio offline intranet deployment profile

## Approved L3 deployment model

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

## Storage note

`STORAGE_BACKEND=local` is valid for offline intranet only when `STORAGE_ROOT`
points to approved internal storage: local server disk, NAS, or a mounted remote
storage volume.

Remote object storage configuration fields exist for deployment planning, but
object-storage I/O must not silently fall back to local storage. Until a real
remote adapter is wired, non-local storage backends fail loudly.

## Health and readiness

- `/health` returns a simple process health response.
- `/ready` validates the deployment profile:
  - offline intranet mode
  - Postgres metadata truth layer
  - SQLite disabled for runtime
  - storage configuration present
  - GigaChat-only provider
  - GigaChat URLs and credentials configured
  - non-default secret key configured

A non-ready profile returns HTTP 503 with explicit errors.
