# Environment validation hardening

R6 adds explicit deployment environment validation for the offline/intranet KW Studio profile.

## Goals

The validator catches unsafe or incomplete deployment configuration before operators start a persistent stack.

It checks:

- required deployment keys are present and non-empty;
- `CHANGE_ME`/placeholder values are replaced in real env files;
- `SECRET_KEY` is strong enough for production;
- `DATABASE_URL` is a Postgres URL when `METADATA_BACKEND=postgres`;
- localhost databases are rejected in `APP_ENV=production` unless explicitly allowed;
- the approved offline profile uses `LLM_PROVIDER=gigachat`;
- GigaChat endpoints are internal HTTP(S) URLs or placeholders in `.env.deploy.example` checks;
- sensitive values are redacted in output.

## Commands

Validate the example file while allowing placeholders:

```bash
python3 scripts/kw_env_validate.py --env-file .env.deploy.example --allow-placeholders
```

Validate a real deployment env file:

```bash
python3 scripts/kw_env_validate.py --env-file .env.deploy --require-offline-profile
```

For local development only, allow a localhost Postgres URL:

```bash
python3 scripts/kw_env_validate.py --env-file .env.deploy --allow-localhost-db
```

## Secret handling

The script never prints raw values for sensitive keys such as:

- `DATABASE_URL`
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `GIGACHAT_CLIENT_SECRET`
- tokens and access keys

It prints `[set]` or `[unset]` for those keys instead.

## Operator rules

- Do not commit `.env.deploy`.
- Do not use `.env.deploy.example` for persistent deployment.
- Replace every `CHANGE_ME` value before running a persistent stack.
- Keep `DEPLOYMENT_MODE=offline_intranet` and `LLM_PROVIDER=gigachat` for the approved local GigaChat profile.
- Use an internal `GIGACHAT_API_BASE_URL` and `GIGACHAT_AUTH_URL` reachable from the backend container.

## Non-goals

R6 does not add Vault, KMS, 1Password, cloud secret managers, auth redesign, or committed real secrets.
