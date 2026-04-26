# P Phase Anti-Scope Prompts Revised

## Purpose

This file is the control layer for Codex/AI patch generation during P phase.

Use it to prevent broad rewrites, stale patching, hidden scope creep, and accidental coupling between issues.

Every prompt should be specific enough that Codex cannot "helpfully" implement the next issue.

---

# Universal P phase anti-scope block

Paste this block into every P phase implementation prompt.

```text
ANTI-SCOPE REVISED — mandatory constraints:
- Implement ONLY the named issue.
- Do NOT implement later P issues.
- Do NOT redesign architecture.
- Do NOT rewrite shared files broadly.
- Do NOT reformat unrelated files.
- Do NOT change public API contracts unless this issue explicitly says so.
- Do NOT change frontend behavior unless this issue explicitly says so.
- Do NOT change backend runtime behavior unless this issue explicitly says so.
- Do NOT introduce new infrastructure requirements unless this issue explicitly says so.
- Do NOT remove existing tests.
- Do NOT weaken existing tests.
- Do NOT silence failing tests by relaxing assertions.
- Do NOT fake external integrations.
- Do NOT print secrets in scripts, logs, fixtures, docs, or tests.
- Do NOT assume files are unchanged from earlier prompts; inspect live files first.
- If an anchor is missing or a file has drifted, stop and report the exact file and reason.
```

---

# Universal current-branch-state block

```text
Work from the repository root.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.
```

---

# Universal file-script delivery block

```text
Patch delivery rule:
- Produce a single Python helper script named apply_p<N>_<short_name>.py.
- The script must be run from repository root.
- The script must fail loudly if expected anchors are missing.
- The script must not modify unrelated files.
- The script must print [PASS]/[OK] messages for applied/idempotent operations.
- The script must not leave temporary helper files in the repository after the user removes it.
```

---

# P1 anti-scope — Real Postgres CI gate

```text
Implement P1 only: real Postgres CI gate.

Allowed:
- Add CI/job/script/docs for running existing Postgres integration tests.
- Add safety checks around KW_POSTGRES_TEST_DATABASE_URL.
- Preserve local skip behavior when DSN is not configured.

Forbidden:
- Do NOT replace SQLite tests.
- Do NOT require Postgres for default local pytest.
- Do NOT change repository persistence behavior unless tests expose a real bug.
- Do NOT add production DB credentials.
- Do NOT print DSN values.
- Do NOT modify frontend.
- Do NOT implement deployment packaging from P6.
- Do NOT implement phase audit from P8.
```

## P1 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py
- scripts/kw_deployment_preflight.py

Implement Issue P1 only: Real Postgres CI gate.

Use a file-script patch named apply_p1_postgres_ci_gate.py.

Hard boundaries:
[paste P1 anti-scope here]

Validation:
- python3 -m pytest backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py -q
- python3 -m pytest -q
- python3 -m compileall backend
```

---

# P2 anti-scope — Frontend E2E deck revision smoke

```text
Implement P2 only: frontend E2E deck revision smoke.

Allowed:
- Add minimal frontend E2E/DOM smoke coverage.
- Mock backend responses where appropriate.
- Verify revision request does not include plan payload.

Forbidden:
- Do NOT redesign UI.
- Do NOT change backend contracts.
- Do NOT require real LLM/PPTX generation.
- Do NOT require real Postgres.
- Do NOT implement version timeline from P3.
- Do NOT implement rollback from P4.
- Do NOT upgrade Next/dependencies unless required for the test runner and explicitly minimal.
```

## P2 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- frontend/package.json
- frontend/src/components/presentations/presentation-registry-panel.tsx
- frontend/src/components/presentations/plan-snapshot-inspector.tsx
- frontend/src/components/presentations/revision-action-panel.tsx
- frontend/src/lib/api/presentations.ts

Implement Issue P2 only: Frontend E2E deck revision smoke.

Use a file-script patch named apply_p2_frontend_e2e_smoke.py.

Hard boundaries:
[paste P2 anti-scope here]

Validation:
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
- run the new frontend E2E/DOM smoke command
- cd .. && python3 -m pytest -q
- python3 -m compileall backend
```

---

# P3 anti-scope — Editable plan version timeline UI

```text
Implement P3 only: editable plan version timeline UI.

Allowed:
- Add version list endpoint if missing.
- Add frontend version timeline panel.
- Allow read-only selected version plan/diff inspection.

Forbidden:
- Do NOT implement rollback/restore.
- Do NOT mutate versions.
- Do NOT add plan editing.
- Do NOT add PPTX rendering preview.
- Do NOT redesign presentation registry.
- Do NOT change revision creation behavior.
- Do NOT implement arbitrary multi-version diff unless explicitly scoped.
```

## P3 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/routes/presentations.py
- backend/app/api/schemas/presentations.py
- backend/app/api/schemas/plan_snapshots.py
- backend/app/services/presentation_catalog_service.py
- frontend/src/components/presentations/presentation-registry-panel.tsx
- frontend/src/components/presentations/plan-snapshot-inspector.tsx

Implement Issue P3 only: Editable plan version timeline UI.

Use a file-script patch named apply_p3_version_timeline_ui.py.

Hard boundaries:
[paste P3 anti-scope here]

Validation:
- backend focused API tests for version list
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
- cd .. && python3 -m pytest -q
- python3 -m compileall backend
```

---

# P4 anti-scope — Revision preview and rollback

```text
Implement P4 only: revision preview and rollback.

Allowed:
- Add safe restore/rollback operation.
- Add backend API and tests.
- Add frontend action only if backend is stable and scope remains contained.

Forbidden:
- Do NOT delete historical versions.
- Do NOT mutate historical version rows.
- Do NOT overwrite stored files.
- Do NOT implement collaborative conflict resolution.
- Do NOT bypass owner/session checks.
- Do NOT implement dependency/security upgrades from P5.
- Do NOT implement deployment packaging from P6.
```

## P4 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/revision.py
- backend/app/services/slides_service/plan_snapshot.py
- backend/app/api/routes/revisions.py
- backend/app/api/routes/presentations.py
- backend/tests/api/test_o2_revision_without_plan_api.py
- backend/tests/api/test_o3_plan_snapshot_inspection_api.py

Implement Issue P4 only: Revision preview and rollback.

Use a file-script patch named apply_p4_revision_rollback.py.

Hard boundaries:
[paste P4 anti-scope here]

Validation:
- focused rollback tests
- python3 -m pytest -q
- python3 -m compileall backend
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
```

---

# P5 anti-scope — Dependency and security hardening

```text
Implement P5 only: dependency and security hardening.

Allowed:
- Review and update frontend dependencies.
- Update lockfile intentionally.
- Document audit results and residual risk.

Forbidden:
- Do NOT add UI features.
- Do NOT change backend runtime logic.
- Do NOT migrate framework major versions unless strictly necessary.
- Do NOT combine with deployment packaging.
- Do NOT silence audit warnings without documentation.
- Do NOT remove package-lock.json.
```

## P5 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- frontend/package.json
- frontend/package-lock.json

Implement Issue P5 only: Dependency and security hardening.

Use a file-script patch only for documentation/config changes. For package manager changes, provide exact npm commands and review resulting lockfile diff.

Hard boundaries:
[paste P5 anti-scope here]

Validation:
- cd frontend && npm ci --no-audit --no-fund --progress=false
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
- cd .. && python3 -m pytest -q
- python3 -m compileall backend
```

---

# P6 anti-scope — Deployment packaging

```text
Implement P6 only: deployment packaging.

Allowed:
- Add Docker/Compose/local deployment docs.
- Add .env.example.
- Wire healthchecks.
- Document volumes and frontend-backend env.

Forbidden:
- Do NOT bake secrets.
- Do NOT require proprietary services for startup.
- Do NOT remove local non-container workflow.
- Do NOT force tests to run only in containers.
- Do NOT add Kubernetes.
- Do NOT implement dependency upgrades from P5.
- Do NOT implement release audit from P8.
```

## P6 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- Makefile
- scripts/kw_deployment_preflight.py
- scripts/kw_operator_smoke.py
- docs/operator-smoke.md
- backend/app/core/config.py
- frontend/package.json

Implement Issue P6 only: Deployment packaging.

Use a file-script patch named apply_p6_deployment_packaging.py.

Hard boundaries:
[paste P6 anti-scope here]

Validation:
- docker compose config, if compose is added
- python3 scripts/kw_deployment_preflight.py --skip-readiness --skip-tests --skip-frontend
- python3 -m pytest -q
- python3 -m compileall backend
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
```

---

# P7 anti-scope — Auth and user-boundary hardening

```text
Implement P7 only: auth and user-boundary hardening.

Allowed:
- Add negative access tests.
- Tighten missing owner/session checks if tests expose gaps.
- Document current auth assumptions.

Forbidden:
- Do NOT implement full auth provider.
- Do NOT add OAuth/SAML.
- Do NOT create a new user database.
- Do NOT break local default-user mode.
- Do NOT change frontend UX unless required for boundary correctness.
- Do NOT add rollback/version timeline features.
```

## P7 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/dependencies.py
- backend/app/api/routes/presentations.py
- backend/app/api/routes/revisions.py
- backend/tests/api/test_n1_presentation_retrieval_api.py
- backend/tests/api/test_o2_revision_without_plan_api.py
- backend/tests/api/test_o3_plan_snapshot_inspection_api.py

Implement Issue P7 only: Auth and user-boundary hardening.

Use a file-script patch named apply_p7_auth_boundary_tests.py.

Hard boundaries:
[paste P7 anti-scope here]

Validation:
- focused auth-boundary API tests
- python3 -m pytest -q
- python3 -m compileall backend
```

---

# P8 anti-scope — Observability and release audit

```text
Implement P8 only: observability and release audit.

Allowed:
- Add P phase integrity/audit script.
- Add focused regression list.
- Add optional smoke/build checks.
- Add docs for release audit.

Forbidden:
- Do NOT mutate repo state.
- Do NOT require network services by default.
- Do NOT print secrets.
- Do NOT duplicate all CI logic if already covered.
- Do NOT add new product features.
- Do NOT change backend/frontend runtime behavior.
```

## P8 prompt skeleton

```text
Work from the repository root.

Read first:
- P_PHASE_ISSUE_PACK.md
- P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- scripts/kw_deployment_preflight.py
- scripts/kw_operator_smoke.py
- docs/operator-smoke.md
- Makefile

Implement Issue P8 only: Observability and release audit.

Use a file-script patch named apply_p8_release_audit.py.

Hard boundaries:
[paste P8 anti-scope here]

Validation:
- python3 scripts/<new_audit_script>.py --help
- python3 scripts/<new_audit_script>.py --lightweight
- python3 -m pytest -q
- python3 -m compileall backend
- cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
```

---

# Codex-specific guardrails

## Prevent "helpful" adjacent work

Bad prompt:

```text
Improve deployment and security.
```

Good prompt:

```text
Implement P6 only. Do not update dependencies, do not add auth, do not add CI, do not add E2E.
```

## Prevent stale patching

Bad prompt:

```text
Patch the file as described earlier.
```

Good prompt:

```text
Inspect the live contents of every file before planning. If anchors differ, stop and report drift.
```

## Prevent test weakening

Bad prompt:

```text
Fix tests.
```

Good prompt:

```text
Do not weaken assertions. If a test fails because the expected contract is wrong, stop and explain before changing the test.
```

## Prevent secret leakage

Bad prompt:

```text
Print env values for debugging.
```

Good prompt:

```text
Print only whether sensitive variables are configured; never print values of DATABASE_URL, SECRET_KEY, tokens, passwords, or client secrets.
```

## Prevent architecture drift

Bad prompt:

```text
Make the system production-ready.
```

Good prompt:

```text
Implement only the files and behavior listed in the issue. Do not introduce new services, frameworks, databases, queues, or auth providers unless explicitly listed.
```

---

# Final P phase review checklist

Before accepting P phase:

```text
- Branch is based on accepted O phase.
- All P issue verdict commits exist.
- Full backend suite passes.
- Frontend build passes.
- Postgres CI/job is documented or active.
- E2E smoke exists or documented as intentionally deferred.
- Dependency/security review completed.
- Deployment packaging docs/scripts are current.
- Auth boundary tests are present.
- Release audit script passes.
- No secrets are printed by scripts/tests.
- git status is clean.
```
