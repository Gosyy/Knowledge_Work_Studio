# KW Studio database migrations

M3 introduces Alembic as the production schema migration workflow for the
Postgres metadata truth layer.

## Scope

Alembic manages the Postgres schema only. SQLite remains a development/test
compatibility backend and is still initialized from `scripts/migrations/` when
explicitly allowed by settings.

## Configuration

Alembic reads the database URL from `backend.app.core.config.Settings`, which in
turn reads `.env`.

Required production setting:

```bash
METADATA_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://kw_studio:<password>@<postgres-host>:5432/kw_studio
```

Do not point Alembic at SQLite. `migrations/env.py` rejects non-Postgres URLs.

## Commands

From the repository root:

```bash
alembic upgrade head
alembic current
alembic history
```

To create a future revision after M3:

```bash
alembic revision -m "describe schema change"
```

Then edit the generated file and run:

```bash
pytest -q
python -m compileall backend
```

## Bootstrap compatibility

`backend/app/integrations/database/bootstrap.py` is preserved for compatibility
with existing tests and bootstrap paths. New production deployments should run
Alembic migrations as the durable Postgres schema evolution path.

Do not remove bootstrap behavior until a later issue explicitly replaces it and
tests prove safe compatibility.
