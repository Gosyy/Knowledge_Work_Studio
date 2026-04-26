# P7 Production readiness final gate

P7 adds a single final gate for the P phase.

The gate is intentionally conservative: it combines static packaging checks, deployment preflight checks, backend tests, frontend build, and Playwright smoke coverage.

## Local command

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root .
```

Makefile shortcut:

```bash
make production-readiness
```

## Fast static check

Use this when editing packaging files or reviewing CI configuration:

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root . --checks-only
```

## What the gate checks

The full gate runs:

```text
required P-phase file presence
forbidden secret marker scan
git diff --check
deployment package validation
deployment preflight static checks
Postgres gate safety checks
backend pytest
backend compileall
frontend production build
frontend E2E smoke
```

## Postgres gate modes

The final gate supports three Postgres modes:

```text
--postgres-mode safety    validates DSN safety only, skips when no DSN is configured
--postgres-mode optional  runs the real Postgres gate when DSN exists, otherwise skips
--postgres-mode required  requires a configured test DSN and fails without it
```

Default is `safety` so the final gate is runnable on local laptops and in normal CI without provisioning a database.

## Clean git mode

For release branches, run:

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root . --require-clean-git
```

This fails if tracked local changes are present.

## CI workflow

P7 adds:

```text
.github/workflows/production-readiness.yml
```

The workflow installs backend dependencies, frontend dependencies, Playwright Chromium, then runs the final gate.

## Scope boundaries

P7 does not deploy the application. It does not require Docker, cloud credentials, TLS, Kubernetes, or a real production database. It is a final verification gate for the repository state.
