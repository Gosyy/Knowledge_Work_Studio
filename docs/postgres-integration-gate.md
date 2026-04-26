# P1 Real Postgres integration gate

P1 adds a real Postgres test gate for the editable deck persistence path introduced in O phase.

## Why this exists

The normal local test suite keeps Postgres integration tests optional. Without a Postgres DSN, the focused tests skip:

```bash
python3 -m pytest backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py -q
```

That is correct for local development, but release confidence needs a repeatable real database gate.

## Main command

```bash
python3 scripts/kw_postgres_integration_gate.py
```

Without a configured DSN this exits successfully with a `[SKIP]` message.

For CI or release gates, require the DSN:

```bash
python3 scripts/kw_postgres_integration_gate.py --require-dsn
```

## Environment

Preferred variable:

```bash
export KW_POSTGRES_TEST_DATABASE_URL='postgresql://kwstudio:kwstudio@localhost:5432/kwstudio_test'
```

Legacy-compatible fallback:

```bash
export POSTGRES_TEST_DATABASE_URL='postgresql://kwstudio:kwstudio@localhost:5432/kwstudio_test'
```

The script never prints the DSN value. It prints only a safe summary:

```text
database name
host
port
whether username/password are configured
```

## Safety checks

By default the gate refuses to run when:

- database name is empty;
- database name is `postgres`, `template0`, or `template1`;
- database name looks production-like: `prod`, `production`, `live`, `main`, `master`;
- database name does not contain one of: `test`, `ci`, `local`, `dev`.

Use this escape hatch only for disposable databases:

```bash
python3 scripts/kw_postgres_integration_gate.py \
  --require-dsn \
  --allow-non-test-database-name
```

## GitHub Actions

The workflow is defined in:

```text
.github/workflows/postgres-integration.yml
```

It starts a Postgres 16 service with database `kwstudio_test`, installs `psycopg[binary]`, and runs:

```bash
python scripts/kw_postgres_integration_gate.py --require-dsn
```

## Local Docker example

```bash
docker run --rm --name kwstudio-postgres-test \
  -e POSTGRES_USER=kwstudio \
  -e POSTGRES_PASSWORD=kwstudio \
  -e POSTGRES_DB=kwstudio_test \
  -p 5432:5432 \
  postgres:16
```

In another terminal:

```bash
export KW_POSTGRES_TEST_DATABASE_URL='postgresql://kwstudio:kwstudio@localhost:5432/kwstudio_test'
python3 -m pip install 'psycopg[binary]>=3.1,<4.0'
python3 scripts/kw_postgres_integration_gate.py --require-dsn
```
