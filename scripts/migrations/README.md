# Migrations (baseline)

This folder contains the minimal migration baseline for KW Studio persistence.

## Baseline files

- `0001_repository_baseline.sql`: Creates the repository tables used by persistence.
- `apply_baseline.py`: Applies the baseline migration to the configured SQLite DB.

## Apply locally

From repository root:

```bash
python scripts/migrations/apply_baseline.py
```

Configuration source: `backend.app.core.config.Settings`
- `REPOSITORY_DB_PATH` determines which SQLite DB file is migrated.
- `MIGRATION_BASELINE_PATH` can override the baseline SQL file path.

The migration is idempotent via the `schema_migrations` tracking table.
