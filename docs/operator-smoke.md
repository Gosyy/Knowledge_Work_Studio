# O8 Deployment hardening and operator smoke scripts

This page describes the lightweight operator checks added for the editable deck productization phase.

## Scripts

```bash
python3 scripts/kw_deployment_preflight.py --skip-tests --skip-frontend
python3 scripts/kw_operator_smoke.py --base-url http://localhost:8000
```

The scripts intentionally avoid printing secret values. Sensitive settings are reported only as configured/not configured.

## Local backend smoke

From the repository root:

```bash
source .venv/bin/activate
make create-dirs
make run
```

In another terminal:

```bash
python3 scripts/kw_operator_smoke.py --base-url http://localhost:8000
```

This checks:

- `GET /health`
- `GET /ready`
- `POST /sessions`
- `GET /sessions/{session_id}/presentations`

Use `--skip-session` when a read-only smoke is required.

## Strict deployment readiness

For approved deployment profiles:

```bash
python3 scripts/kw_deployment_preflight.py --strict-ready --require-clean-git
```

`--strict-ready` fails unless the deployment readiness contract evaluates to `ready`.

## Frontend smoke

After starting the frontend:

```bash
python3 scripts/kw_operator_smoke.py \
  --base-url http://localhost:8000 \
  --frontend-url http://localhost:3000
```

## Full release gate

For release candidates:

```bash
python3 scripts/kw_deployment_preflight.py \
  --strict-ready \
  --require-clean-git \
  --run-backend-tests \
  --run-frontend-build
```

The frontend build requires dependencies to be installed first:

```bash
cd frontend
npm ci --no-audit --no-fund --progress=false
```
