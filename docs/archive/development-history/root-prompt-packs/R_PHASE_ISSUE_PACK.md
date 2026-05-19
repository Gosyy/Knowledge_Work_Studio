# R Phase Issue Pack — Full-stack deployment verification and operator-grade hardening

## Phase identity

Branch: `6_Stage_R`
Base: current `main` after merged O + P phases.
Theme: make the deployable KW Studio stack verifiable, operable, observable, and safer without expanding product scope.

R phase starts from the baseline where O + P are already merged:
- editable presentation plan snapshots;
- revision API without explicit plan payload;
- plan inspection/diff/version timeline;
- non-destructive restore;
- hardened artifact metadata/downloads;
- frontend E2E smoke;
- deployment packaging;
- production readiness final gate.

## Global operating rules

All R issues must use the file-script workflow.

Implementation patches must be delivered as repo-root Python apply scripts:
- `apply_rX_<short_slug>.py`;
- validate repository root;
- validate expected branch when appropriate;
- print `[PASS]` or `[OK]` for every changed file/block;
- fail loudly when anchors are missing;
- stay deterministic and reviewable;
- never print secrets;
- never require network access for normal script execution.

Every issue must preserve accepted O/P contracts unless the issue explicitly scopes a compatible hardening patch.

Minimum validation pattern:

```bash
python3 -m pytest <focused tests> -q
python3 -m pytest -q
python3 -m compileall backend
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build && cd ..
git status --short
git diff --stat
```

For deployment/final-gate work:

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R1 — Real full-stack Docker Compose smoke gate

## Goal

Add a real full-stack Docker Compose smoke gate for the deployment package created in P6.

## Scope

Add:
- script to build/start/verify/stop the compose stack;
- optional/manual GitHub workflow;
- docs;
- tests that do not require Docker for normal pytest.

Candidate files:

```text
scripts/kw_fullstack_compose_smoke.py
.github/workflows/fullstack-compose-smoke.yml
docs/fullstack-compose-smoke.md
backend/tests/smoke/test_r1_fullstack_compose_smoke.py
Makefile
```

## Requirements

The script should:
1. check Docker and Docker Compose availability;
2. support `--check-only`;
3. create or validate safe deployment env input;
4. build with `docker compose -f docker-compose.deploy.yml build`;
5. start with `docker compose -f docker-compose.deploy.yml up -d`;
6. poll backend `/health` and `/ready`;
7. optionally poll frontend `/`;
8. run `scripts/kw_operator_smoke.py`;
9. collect compose status/log hints on failure;
10. cleanup unless `--keep-running` is passed;
11. never print secrets.

## Non-goals

No Kubernetes, cloud deployment, TLS, reverse proxy, secret manager, or storage redesign.

## Acceptance checks

```bash
python3 -m pytest backend/tests/smoke/test_r1_fullstack_compose_smoke.py -q
python3 scripts/kw_fullstack_compose_smoke.py --help
python3 scripts/kw_fullstack_compose_smoke.py --check-only
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

Optional when Docker exists:

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --timeout 180
```

---

# R2 — Postgres schema lifecycle and migration preflight

## Goal

Make database schema readiness explicit before deployment.

## Scope

Add:
- schema inventory/preflight script;
- read-only validation mode;
- safe table/column checks;
- docs;
- tests.

Candidate files:

```text
scripts/kw_schema_preflight.py
docs/schema-lifecycle.md
backend/tests/smoke/test_r2_schema_preflight.py
```

## Requirements

The script should:
1. detect metadata backend;
2. validate required tables;
3. validate critical columns;
4. avoid destructive changes;
5. include `--explain`;
6. include `--require-ready`;
7. redact DSN credentials.

## Non-goals

No Alembic migration framework unless explicitly requested. No destructive migrations. No automatic production mutations.

## Acceptance checks

```bash
python3 -m pytest backend/tests/smoke/test_r2_schema_preflight.py -q
python3 scripts/kw_schema_preflight.py --help
python3 scripts/kw_schema_preflight.py --repo-root . --explain
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R3 — Artifact download UI and export history panel

## Goal

Expose P5 hardened artifact delivery in frontend UX.

## Scope

Add:
- frontend artifact API client;
- artifact/export history panel;
- E2E smoke;
- docs.

Candidate files:

```text
frontend/src/lib/api/artifacts.ts
frontend/src/lib/api/artifacts.contract.ts
frontend/src/components/artifacts/artifact-history-panel.tsx
frontend/tests/e2e/artifact-download-smoke.spec.ts
docs/artifact-download-ui.md
```

## Requirements

The UI should:
1. list artifacts by session;
2. show filename, type, size, created time;
3. expose `download_url`;
4. never show `storage_key`, `storage_uri`, or local paths;
5. handle empty/error states.

## Non-goals

No artifact generation changes, storage backend changes, signed URLs, or bulk export.

## Acceptance checks

```bash
cd frontend
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e:smoke
cd ..
python3 -m pytest backend/tests/api/test_p5_artifact_delivery_hardening.py -q
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R4 — Restore audit metadata and safer confirmation UX

## Goal

Harden P4 non-destructive restore with auditability and safer confirmation UX.

## Scope

Add:
- targeted restore audit metadata where current model permits;
- frontend confirmation modal/panel improvement;
- tests preserving non-destructive semantics;
- docs.

Candidate files:

```text
backend/app/services/slides_service/revision.py
backend/app/api/routes/revisions.py
backend/app/api/schemas/revisions.py
backend/tests/api/test_r4_restore_audit.py
frontend/src/components/presentations/version-timeline-panel.tsx
frontend/tests/e2e/version-restore-audit-smoke.spec.ts
docs/restore-audit.md
```

## Requirements

Preserve:
- restore creates a new version;
- history is not mutated;
- target plan snapshot is copied;
- owner scope remains enforced.

Add:
- explicit actor/change reason handling where safe;
- stricter summary/reason validation;
- deliberate UI confirmation;
- regression coverage.

## Non-goals

No destructive rollback, branch/DAG editor, collaborative conflict system, or auth redesign.

## Acceptance checks

```bash
python3 -m pytest backend/tests/api/test_p4_revision_restore_api.py backend/tests/api/test_r4_restore_audit.py -q
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build && npm run test:e2e:smoke && cd ..
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R5 — Operator deployment runbook, backup, and restore drill

## Goal

Turn deployment packaging into an operator runbook with safe backup/restore drills.

## Scope

Add:
- operator runbook;
- backup dry-run script;
- restore-check script/guidance;
- tests for command generation and redaction.

Candidate files:

```text
scripts/kw_operator_backup.py
scripts/kw_operator_restore_check.py
docs/operator-runbook.md
docs/backup-restore.md
backend/tests/smoke/test_r5_operator_backup_scripts.py
```

## Requirements

Scripts should:
1. support `--dry-run`;
2. avoid secret printing;
3. generate Postgres backup command hints;
4. generate artifact volume backup command hints;
5. avoid destructive restore by default.

## Non-goals

No cloud backups, S3/GCS, cron scheduler, or actual destructive restore automation.

## Acceptance checks

```bash
python3 -m pytest backend/tests/smoke/test_r5_operator_backup_scripts.py -q
python3 scripts/kw_operator_backup.py --help
python3 scripts/kw_operator_backup.py --dry-run
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R6 — Environment and secret validation hardening

## Goal

Make deployment environment validation stricter and safer.

## Scope

Add:
- env validation script;
- placeholder detection;
- SECRET_KEY strength check;
- DATABASE_URL safety classification;
- integration with preflight/final gate if narrow;
- docs/tests.

Candidate files:

```text
scripts/kw_env_validate.py
docs/environment-validation.md
backend/tests/smoke/test_r6_env_validation.py
scripts/kw_deployment_preflight.py
scripts/kw_production_readiness_gate.py
```

## Requirements

Detect:
- `CHANGE_ME`;
- empty required values;
- weak `SECRET_KEY`;
- localhost DB in production unless explicitly allowed;
- obvious DATABASE_URL/env mismatch where practical;
- accidental secret printing risk.

## Non-goals

No Vault/KMS/1Password integration, no auth redesign, no committing real env files.

## Acceptance checks

```bash
python3 -m pytest backend/tests/smoke/test_r6_env_validation.py -q
python3 scripts/kw_env_validate.py --help
python3 scripts/kw_env_validate.py --env-file .env.deploy.example --allow-placeholders
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R7 — Observability baseline: logs, health, ready, diagnostics

## Goal

Improve operator debugging without adding a full observability stack.

## Scope

Add:
- safe diagnostic CLI;
- structured health/ready details where appropriate;
- logging baseline;
- tests/docs.

Candidate files:

```text
backend/app/api/routes/health.py
backend/app/core/logging.py
scripts/kw_runtime_diagnostics.py
docs/observability-baseline.md
backend/tests/api/test_r7_health_diagnostics.py
backend/tests/smoke/test_r7_runtime_diagnostics.py
```

## Requirements

Diagnostics should:
1. not print secrets;
2. show metadata backend;
3. show storage backend;
4. show deployment mode;
5. show required path presence;
6. preserve existing `/health` behavior;
7. keep `/ready` useful for deployment checks.

## Non-goals

No Prometheus/Grafana stack, OpenTelemetry collector, external log shipping, or distributed tracing.

## Acceptance checks

```bash
python3 -m pytest backend/tests/api/test_r7_health_diagnostics.py backend/tests/smoke/test_r7_runtime_diagnostics.py -q
python3 scripts/kw_runtime_diagnostics.py --repo-root .
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

# R8 — Dependency and security baseline refresh

## Goal

Stabilize dependency/security posture after P phase.

## Scope

Add:
- controlled frontend dependency update, especially Next.js if safe;
- package-lock update;
- documented dependency policy;
- optional no-network audit wrapper/tests.

Candidate files:

```text
frontend/package.json
frontend/package-lock.json
docs/dependency-security-baseline.md
scripts/kw_dependency_audit.py
backend/tests/smoke/test_r8_dependency_audit.py
```

## Requirements

R8 should:
1. avoid broad dependency churn;
2. keep frontend build green;
3. keep Playwright smoke green;
4. document upgrade decision;
5. keep production readiness gate green.

## Non-goals

No framework migration, no React major churn unless required, no UI redesign.

## Acceptance checks

```bash
cd frontend
npm install --no-audit --no-fund --progress=false
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e:smoke
cd ..
python3 -m pytest backend/tests/smoke/test_r8_dependency_audit.py -q
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

---

## Recommended order

```text
R1  Real full-stack Docker Compose smoke gate
R2  Postgres schema lifecycle and migration preflight
R3  Artifact download UI and export history panel
R4  Restore audit metadata and safer confirmation UX
R5  Operator deployment runbook, backup, and restore drill
R6  Environment and secret validation hardening
R7  Observability baseline
R8  Dependency and security baseline refresh
```

## Phase completion criteria

R phase can be accepted when:
- every R issue has a functional commit and an empty verdict commit;
- final production readiness gate passes on `6_Stage_R`;
- full-stack compose smoke is documented and either passes or explicitly skips for unavailable Docker;
- no public API reintroduces storage path leakage;
- no scripts print secrets;
- frontend build and E2E smoke pass;
- branch is clean and ready for PR into `main`.
