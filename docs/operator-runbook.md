# Operator deployment runbook

This runbook is the R5 operator checklist for a local/offline KW Studio deployment.

## Scope

R5 documents the current Docker Compose deployment path and adds dry-run backup and
restore-check helpers. It does not introduce cloud backups, cron scheduling, S3/GCS,
or destructive restore automation.

## Before deployment

1. Confirm the branch and accepted phase verdicts.
2. Keep real secrets out of Git.
3. Copy `.env.deploy.example` to `.env.deploy`.
4. Replace every `CHANGE_ME` value.
5. Keep the default offline deployment posture unless a later accepted issue changes it:
   - `DEPLOYMENT_MODE=offline_intranet`
   - `METADATA_BACKEND=postgres`
   - `STORAGE_BACKEND=local`
   - `LLM_PROVIDER=gigachat`

## Preflight

Run the production readiness gate before operating a persistent deployment:

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

On machines with local proxy variables that interfere with Playwright localhost checks,
run the gate with localhost proxy variables unset:

```bash
env \
  -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  -u http_proxy -u https_proxy -u all_proxy \
  NO_PROXY=127.0.0.1,localhost \
  no_proxy=127.0.0.1,localhost \
  python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## Start deployment

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio up -d --build
```

Check status:

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio ps
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/ready
```

## Backup dry-run

Generate a reviewable backup plan without executing it:

```bash
python3 scripts/kw_operator_backup.py --dry-run --repo-root .
```

The dry-run prints command hints for:

- Postgres custom-format dump creation;
- copying the dump to a local backup directory;
- read-only artifact volume archive creation;
- checksum recording.

The script redacts secrets and does not execute commands.

## Restore check dry-run

Generate a non-destructive restore-check plan:

```bash
python3 scripts/kw_operator_restore_check.py --dry-run --repo-root . --backup-dir backups/latest
```

The restore-check plan only inspects backup files. It does not restore into a
database, mutate a Docker volume, or extract artifacts.

## Stop deployment

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio down
```

Do not use `--volumes` for a persistent deployment unless the operator has a verified
backup and explicitly intends to remove the local Postgres and artifact volumes.
