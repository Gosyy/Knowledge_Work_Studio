# Observability baseline

R7 adds an operator-grade diagnostics baseline without introducing a full observability stack.

## Goals

- Preserve the existing `/health` contract: `{"status": "ok"}`.
- Keep `/ready` focused on deployment readiness and safe operator fields.
- Provide a local diagnostic CLI that is safe to run in offline/intranet environments.
- Never print secrets or raw database credentials.
- Keep diagnostics dependency-light and suitable for support runbooks.

## Runtime diagnostics CLI

Run:

```bash
python3 scripts/kw_runtime_diagnostics.py --repo-root .
```

Useful variants:

```bash
python3 scripts/kw_runtime_diagnostics.py --repo-root . --json
python3 scripts/kw_runtime_diagnostics.py --repo-root . --require-paths
python3 scripts/kw_runtime_diagnostics.py --repo-root . --env-file .env.deploy
```

The command reports:

- `deployment_mode`
- `metadata_backend`
- `storage_backend`
- `llm_provider`
- database URL classification, not the raw URL
- required runtime/deployment path presence
- selected environment keys with secrets redacted

## Redaction policy

The diagnostics CLI redacts keys containing:

- `SECRET`
- `PASSWORD`
- `TOKEN`
- `ACCESS_KEY`
- `API_KEY`
- `CLIENT_SECRET`
- `DATABASE_URL`

Redacted values are printed as `[set]` or `[unset]`.

## Health and readiness

`/health` remains intentionally minimal so load balancers, smoke gates, and scripts can depend on the stable payload.

`/ready` continues to expose readiness status, deployment mode, metadata backend, storage backend, LLM provider, check booleans, warnings, and errors. It must not expose secrets.

## Non-goals

R7 does not add:

- Prometheus or Grafana;
- OpenTelemetry collector;
- external log shipping;
- distributed tracing;
- a metrics storage backend;
- a production log aggregation stack.
