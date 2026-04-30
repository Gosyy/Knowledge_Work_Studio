# Postgres schema lifecycle and migration preflight

R2 adds a read-only schema preflight for KW Studio deployments.

The goal is to make schema readiness explicit before deployment without
introducing destructive migrations or a new migration framework.

## Scope

This check validates the expected Postgres metadata schema used by the current
repository layer.

It covers critical tables and columns for:

- users
- sessions
- tasks
- artifacts
- uploaded files
- stored files
- documents and document versions
- presentations and presentation versions
- presentation plan snapshots
- artifact sources
- derived contents

## Non-goals

R2 does not add:

- Alembic;
- destructive migrations;
- automatic production schema mutation;
- data backfills;
- database redesign;
- cloud database management.

## Static mode

Static mode validates the internal schema manifest and prints the expected
table/column inventory.

```bash
python3 scripts/kw_schema_preflight.py --repo-root . --explain
```

This mode does not require Docker, psycopg, or a live Postgres database.

## Live mode

Live mode checks the actual database schema through `information_schema`.

```bash
DATABASE_URL=postgresql://user:password@host:5432/db \
python3 scripts/kw_schema_preflight.py --repo-root . --check-live
```

Sensitive DSN fields are never printed. Output only reports host, port,
database name, and whether username/password were configured.

## Required ready mode

Required mode is for operator-controlled deployment checks where a live
Postgres database must exist and match the schema manifest.

```bash
DATABASE_URL=postgresql://user:password@host:5432/db \
python3 scripts/kw_schema_preflight.py --repo-root . --require-ready
```

If `DATABASE_URL` is missing, psycopg is unavailable, the backend is not
Postgres, or a table/column is missing, the command fails.

## Production readiness gate integration

The production readiness gate runs the schema preflight in static explain mode:

```bash
python3 scripts/kw_schema_preflight.py --repo-root . --explain
```

The existing real Postgres integration gate remains separate. R2 does not make
ordinary pytest or the default production readiness gate depend on Docker or a
live Postgres instance.

## Operator interpretation

- `[PASS] static Postgres schema manifest ...` means the expected schema
  inventory is internally valid.
- `[PASS] schema preflight completed in static mode` means no live database was
  required for this run.
- `[PASS] live Postgres schema is ready` means the database contains all
  required tables and critical columns.
- `[FAIL] missing table: ...` or `[FAIL] missing column: ...` means deployment
  should stop until the schema is corrected.

## Safety rules

- The preflight is read-only.
- It only queries `information_schema` in live mode.
- It never writes, migrates, truncates, deletes, or backfills data.
- It never prints database credentials.
