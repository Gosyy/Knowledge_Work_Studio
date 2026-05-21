# Full-stack Docker Compose smoke gate

R1 adds a real full-stack smoke gate for the deployable KW Studio Docker Compose package.

The gate is intentionally operator-focused and manual. It verifies that the deployment package can be built, started, checked, and stopped without expanding the product scope or introducing new infrastructure.

## What it checks

`scripts/kw_fullstack_compose_smoke.py` performs the following steps:

1. validates that deployment packaging files are present;
2. validates an existing `.env.deploy`, or creates a local ephemeral one for the smoke run;
3. checks Docker and Docker Compose availability;
4. runs `docker compose -f docker-compose.deploy.yml build`;
5. runs `docker compose -f docker-compose.deploy.yml up -d`;
6. catches backend image/runtime import failures such as missing packaged `skills/` modules;
7. polls backend `/health` and `/ready`;
8. optionally polls the frontend root page;
9. runs `scripts/kw_operator_smoke.py` against the running stack;
10. prints compose status and log hints on failure;
11. stops the stack and removes smoke volumes unless `--keep-running` or `--preserve-volumes` is used.

The script redacts values for secret-looking keys before printing captured command output. It must not be used as a secret management system; it is a smoke gate only.

## Static check

This command does not require a working Docker daemon. It reports Docker availability as warnings when Docker is absent, validates the local repository shape, and validates `.env.deploy` when that file exists.

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --check-only
```

## Real smoke run

Run this from the repository root on a machine with Docker and the Docker Compose plugin:

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --timeout 180
```

Equivalent Make targets:

```bash
make fullstack-compose-smoke-check
make fullstack-compose-smoke
```

## Environment handling

The deployment compose file expects `.env.deploy`.

If `.env.deploy` already exists, the smoke script validates required keys and fails on placeholder values such as `CHANGE_ME`.

If `.env.deploy` does not exist, the script creates a local ephemeral file with smoke-only values, uses it for the compose run, and removes it during cleanup. The file is not intended to be committed.

The generated smoke environment satisfies the existing `/ready` contract by using `DEPLOYMENT_MODE=offline_intranet`, `METADATA_BACKEND=postgres`, `LLM_PROVIDER=gigachat`, non-empty smoke-only GigaChat endpoint placeholders, and generated secret values. These smoke values are for readiness verification only and are removed with the generated `.env.deploy` during cleanup.

The smoke env also pins local storage to `/app/storage` with uploads, artifacts, and temp directories under that path. This matches the `kw_storage:/app/storage` named volume and prevents the non-root backend container from trying to create the default `/srv/kw_studio` tree during operator smoke.

For a persistent deployment, copy `.env.deploy.example` to `.env.deploy` and replace all placeholders before running Docker Compose directly.

## Ports

The generated smoke environment uses backend port `8000` and frontend port `3000` by default. Override them when those ports are already occupied:

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --backend-port 8010 --frontend-port 3010 --timeout 180
```

## Failure handling

While polling endpoints, the script prints periodic wait messages so a slow `/ready` check does not look like a silent hang.

On failure the script prints:

- the failing step;
- `docker compose ps` output;
- the tail of compose logs;
- redacted command output where secret-looking values are replaced with `[REDACTED]`.

The default cleanup command is equivalent to:

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio-r1-smoke down --remove-orphans --volumes
```

Use `--keep-running` only when you want to inspect containers manually after a smoke run.

## R1 acceptance commands

```bash
python3 -m pytest backend/tests/smoke/test_r1_fullstack_compose_smoke.py -q
python3 scripts/kw_fullstack_compose_smoke.py --help
python3 scripts/kw_fullstack_compose_smoke.py --check-only
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

Optional when Docker exists:

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --timeout 180
```

## Non-goals

R1 does not add Kubernetes, cloud deployment, TLS, a reverse proxy, a production secret manager, or any storage redesign.
