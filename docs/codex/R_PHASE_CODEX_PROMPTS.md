# R Phase Codex Prompts

Use these prompts one at a time. Do not combine R steps.

## Universal R prompt prefix

```text
Work from repository root on branch 6_Stage_R.

Before planning, verify the previous accepted verdict with:
git fetch origin
git pull --ff-only
git log --oneline -8
git status --short

Implement this R issue only.

Use a repo-root Python apply script:
apply_rX_<slug>.py

The script must validate repo root, inspect live file anchors, fail loudly on
missing anchors, print [PASS]/[OK] for each changed block, avoid network access,
and never print secrets.

Do not output a giant diff directly in chat.

Preserve accepted O/P/R contracts.
Do not weaken tests.
Do not print or commit secrets.
Do not introduce infrastructure outside allowed scope.
```

## R2 — Postgres schema lifecycle and migration preflight

```text
Implement R2 only: Postgres schema lifecycle and migration preflight.

Goal:
Make database schema readiness explicit before deployment.

Allowed files:
- scripts/kw_schema_preflight.py
- docs/schema-lifecycle.md
- backend/tests/smoke/test_r2_schema_preflight.py
- narrow integration into existing preflight/final gate only if minimal and justified

Requirements:
1. detect metadata backend;
2. validate required tables;
3. validate critical columns;
4. avoid destructive changes;
5. support --explain;
6. support --require-ready;
7. redact DSN credentials;
8. work without requiring a live Postgres connection for normal unit tests;
9. provide deterministic output suitable for operator use.

Forbidden:
- no Alembic framework unless explicitly requested;
- no destructive migrations;
- no production schema mutation;
- no data backfill;
- no DB schema redesign;
- no DSN credential printing.

Acceptance:
python3 -m pytest backend/tests/smoke/test_r2_schema_preflight.py -q
python3 scripts/kw_schema_preflight.py --help
python3 scripts/kw_schema_preflight.py --repo-root . --explain
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R3 — Artifact download UI and export history panel

```text
Implement R3 only: artifact download UI and export history panel.

Goal:
Expose existing hardened artifact delivery in frontend UX.

Allowed files:
- frontend/src/lib/api/artifacts.ts
- frontend/src/lib/api/artifacts.contract.ts
- frontend/src/components/artifacts/artifact-history-panel.tsx
- frontend/tests/e2e/artifact-download-smoke.spec.ts
- docs/artifact-download-ui.md
- narrow route/page integration if needed

Requirements:
1. list artifacts by session;
2. show filename, type, size, created time;
3. expose download_url;
4. handle empty and error states;
5. keep API calls in dedicated client modules;
6. add E2E smoke with mocked or stable test API behavior.

Forbidden:
- no artifact generation changes;
- no storage backend changes;
- no signed URL system;
- no bulk export;
- no exposing storage_key, storage_uri, local paths, or internal storage IDs;
- no unrelated UI redesign.

Acceptance:
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build && npm run test:e2e:smoke && cd ..
python3 -m pytest backend/tests/api/test_p5_artifact_delivery_hardening.py -q
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R4 — Restore audit metadata and safer confirmation UX

```text
Implement R4 only: restore audit metadata and safer confirmation UX.

Goal:
Harden non-destructive presentation version restore with auditability and
deliberate confirmation.

Allowed files:
- backend/app/services/slides_service/revision.py
- backend/app/api/routes/revisions.py
- backend/app/api/schemas/revisions.py
- backend/tests/api/test_r4_restore_audit.py
- frontend/src/components/presentations/version-timeline-panel.tsx
- frontend/tests/e2e/version-restore-audit-smoke.spec.ts
- docs/restore-audit.md

Must preserve:
- restore creates a new version;
- history is not mutated;
- target plan snapshot is copied;
- owner scope remains enforced.

Add:
- actor/change reason handling where current model permits;
- stricter summary/reason validation;
- deliberate UI confirmation;
- regression coverage.

Forbidden:
- no destructive rollback;
- no deleting versions;
- no mutating historical versions;
- no branch/DAG editor;
- no collaborative conflict system;
- no auth redesign.

Acceptance:
python3 -m pytest backend/tests/api/test_p4_revision_restore_api.py backend/tests/api/test_r4_restore_audit.py -q
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build && npm run test:e2e:smoke && cd ..
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R5 — Operator deployment runbook, backup, and restore drill

```text
Implement R5 only: operator runbook, backup, and restore drill.

Goal:
Turn deployment packaging into an operator runbook with safe backup/restore
drills.

Allowed files:
- scripts/kw_operator_backup.py
- scripts/kw_operator_restore_check.py
- docs/operator-runbook.md
- docs/backup-restore.md
- backend/tests/smoke/test_r5_operator_backup_scripts.py

Requirements:
1. support --dry-run;
2. avoid secret printing;
3. generate Postgres backup command hints;
4. generate artifact volume backup command hints;
5. avoid destructive restore by default;
6. document offline/intranet constraints;
7. mention three-server topology only as documentation, not runtime code.

Forbidden:
- no cloud backup;
- no S3/GCS;
- no cron scheduler;
- no external backup vendor;
- no destructive restore automation by default;
- no secret printing.

Acceptance:
python3 -m pytest backend/tests/smoke/test_r5_operator_backup_scripts.py -q
python3 scripts/kw_operator_backup.py --help
python3 scripts/kw_operator_backup.py --dry-run
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R6 — Environment and secret validation hardening

```text
Implement R6 only: environment and secret validation hardening.

Goal:
Make deployment environment validation stricter and safer.

Allowed files:
- scripts/kw_env_validate.py
- docs/environment-validation.md
- backend/tests/smoke/test_r6_env_validation.py
- scripts/kw_deployment_preflight.py
- scripts/kw_production_readiness_gate.py

Requirements:
Detect:
1. CHANGE_ME placeholders;
2. empty required values;
3. weak SECRET_KEY;
4. localhost DB in production unless explicitly allowed;
5. obvious DATABASE_URL/env mismatch where practical;
6. accidental secret printing risk;
7. offline/intranet endpoint violations where narrow and safe.

Offline rules:
- DEPLOYMENT_MODE=offline_intranet must not point default LLM endpoints to public internet.
- Local GigaChat endpoint must be internal ip:port or explicit allowlist.
- Do not require LiteLLM for default production mode.

Forbidden:
- no Vault/KMS/1Password integration;
- no auth redesign;
- no storing secrets in repository;
- no printing secret values.

Acceptance:
python3 -m pytest backend/tests/smoke/test_r6_env_validation.py -q
python3 scripts/kw_env_validate.py --help
python3 scripts/kw_env_validate.py --env-file .env.deploy.example --allow-placeholders
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R7 — Observability baseline

```text
Implement R7 only: logs, health, ready, and diagnostics baseline.

Goal:
Improve operator debugging without adding a full observability stack.

Allowed files:
- backend/app/api/routes/health.py
- backend/app/core/logging.py
- scripts/kw_runtime_diagnostics.py
- docs/observability-baseline.md
- backend/tests/api/test_r7_health_diagnostics.py
- backend/tests/smoke/test_r7_runtime_diagnostics.py

Requirements:
Diagnostics should:
1. not print secrets;
2. show metadata backend;
3. show storage backend;
4. show deployment mode;
5. show required path presence;
6. preserve existing /health behavior;
7. keep /ready useful for deployment checks;
8. include LLM provider topology as redacted high-level status only if safe.

Forbidden:
- no Prometheus/Grafana stack;
- no OpenTelemetry collector;
- no external log shipping;
- no distributed tracing;
- no secret exposure.

Acceptance:
python3 -m pytest backend/tests/api/test_r7_health_diagnostics.py backend/tests/smoke/test_r7_runtime_diagnostics.py -q
python3 scripts/kw_runtime_diagnostics.py --repo-root .
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## R8 — Dependency and security baseline refresh

```text
Implement R8 only: dependency and security baseline refresh.

Goal:
Stabilize dependency/security posture after P/R phases.

Allowed files:
- frontend/package.json
- frontend/package-lock.json
- docs/dependency-security-baseline.md
- scripts/kw_dependency_audit.py
- backend/tests/smoke/test_r8_dependency_audit.py

Requirements:
1. avoid broad dependency churn;
2. keep frontend build green;
3. keep Playwright smoke green;
4. document upgrade decision;
5. keep production readiness gate green;
6. support no-network audit/reporting mode if added.

Forbidden:
- no framework migration;
- no broad dependency churn;
- no React major upgrade unless explicitly required;
- no UI redesign;
- no backend dependency churn unrelated to security baseline.

Acceptance:
python3 -m pytest backend/tests/smoke/test_r8_dependency_audit.py -q
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build && npm run test:e2e:smoke && cd ..
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```
