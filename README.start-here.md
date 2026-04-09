# KW Studio — Start Here

This repository is prepared so Codex can start from a structured, non-empty codebase.

## Included
- backend FastAPI bootstrap
- backend health test
- docs and Codex guidance
- modular-monolith backend package boundaries for domain, orchestrator, services, repositories, integrations, and runtime
- empty product directories for frontend, infra, skills, and storage

## First local run

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
make create-dirs
make test
make run
```

Health check:
- http://localhost:8000/health

## Database bootstrap and migration baseline (A2)

KW Studio now bootstraps a local SQLite metadata database on backend startup.

- DB file path: `SQLITE_DB_PATH` (default: `./storage/metadata.sqlite3`)
- Migration directory: `SQLITE_MIGRATIONS_DIR` (default: `./scripts/migrations`)
- Baseline migration file: `scripts/migrations/0001_baseline.sql`

How startup works:
1. App startup creates the SQLite DB file directory if needed.
2. App startup ensures a `schema_migrations` tracking table exists.
3. App startup applies any `*.sql` migrations from `SQLITE_MIGRATIONS_DIR` in filename order.
4. Applied migration filenames are recorded so reruns are idempotent.

To run with defaults:
```bash
cp .env.example .env
make run
```

To reset local metadata DB during development:
```bash
rm -f ./storage/metadata.sqlite3
make run
```

## First Codex run

Use Prompt 1 from your prepared Codex prompt pack.
