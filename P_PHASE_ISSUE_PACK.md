# P Phase Issue Pack — Production CI, E2E, deployment packaging, rollback/version hardening

## Phase name

P phase: production hardening after editable deck productization.

## Current baseline

This phase starts from branch:

```text
5_Stage_P
```

Expected ancestry:

```text
5_Stage_P
└── ceb6b6f O8 verdict: ACCEPT
    └── 4_Stage_O complete
```

O phase delivered:

- editable `PresentationPlan` snapshot persistence;
- revision API without explicit plan payload;
- plan snapshot retrieval and diff inspection API;
- frontend presentation registry;
- frontend plan snapshot/diff inspector;
- frontend revision action UI;
- deployment preflight and operator smoke scripts.

P phase must harden this into a safer product/deployment track without redesigning the application.

## Global rules for every P issue

### Current-branch-state rules

Every implementation prompt must include these rules verbatim or semantically unchanged:

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

### Patch transport rule

All P phase patches must be delivered as repository-root Python helper scripts, not as huge pasted shell heredocs.

Expected local workflow:

```bash
cd ~/workplace/Knowledge_Work_Studio

cp ~/Загрузки/apply_pX_<short_name>.py ./apply_pX_<short_name>.py
python3 apply_pX_<short_name>.py
rm -f apply_pX_<short_name>.py
```

The helper script must be idempotent where reasonable and must fail loudly if expected anchors are missing.

### Validation rule

Every P issue must have focused validation plus a full final gate unless explicitly impossible.

Minimum gate:

```bash
python3 -m pytest -q
python3 -m compileall backend
cd frontend && NEXT_TELEMETRY_DISABLED=1 npm run build
```

For backend-only issues, frontend build may still be run as a regression gate if frontend files exist and dependencies are installed.

### Commit rule

Every issue gets a functional commit plus a verdict commit only after green validation:

```bash
git commit -m "P<N> <short description>"
git push origin 5_Stage_P

git commit --allow-empty -m "P<N> verdict: ACCEPT"
git push origin 5_Stage_P
```

### Scope rule

Do not combine adjacent P issues. If a tempting improvement appears, document it under "next phase / future issue" rather than implementing it opportunistically.

---

# Issue P1 — Real Postgres CI gate

## Goal

Make the O4 Postgres integration tests runnable as a first-class CI/job contract instead of being only local/skipped tests.

## Problem

O4 added honest Postgres tests that skip without `KW_POSTGRES_TEST_DATABASE_URL`. That is correct locally, but production confidence needs a real Postgres gate.

## Scope

Implement repository/CI-facing support to run existing Postgres integration tests against a real test database.

Allowed work:

- Add CI workflow/job or documented script for Postgres integration tests.
- Add operator/dev documentation for `KW_POSTGRES_TEST_DATABASE_URL`.
- Add a focused test marker or script entrypoint if the project needs one.
- Keep existing skip behavior when no DSN is configured.
- Ensure tests do not run against production database URLs accidentally.
- Add safety checks that reject suspicious database names if feasible.

Recommended files:

```text
.github/workflows/*
docs/*
scripts/*
backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py
```

## Hard boundaries

- Do not modify production repository logic unless a test exposes a real defect.
- Do not replace SQLite tests with Postgres-only tests.
- Do not require local developers to run Postgres by default.
- Do not add external managed DB dependencies.
- Do not print database credentials in logs.
- Do not change O1/O2/O3 API contracts.

## Acceptance criteria

- There is a repeatable command/job for real Postgres integration tests.
- Existing local `python3 -m pytest -q` still passes/skips appropriately without DSN.
- CI or script clearly distinguishes "no DSN" from "Postgres test failed".
- Documentation explains safe local use.
- Full backend suite remains green.

## Suggested focused tests

```bash
python3 -m pytest backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py -q
python3 -m pytest -q
python3 -m compileall backend
```

---

# Issue P2 — Frontend E2E deck revision smoke

## Goal

Add a real browser-level smoke path for the editable deck workflow.

## Problem

O5/O6/O7 passed Next build and TypeScript validation, but there is no browser-level test proving the user can use the workflow end-to-end.

## Scope

Add a small E2E smoke suite that covers:

- app shell renders;
- presentation registry panel exists;
- session id can be entered;
- frontend calls presentation registry endpoint;
- selected presentation metadata renders;
- plan inspector controls are visible;
- revision action form can be filled;
- request payload for revision action does not contain `plan`.

Recommended approach:

- Prefer Playwright if it is already acceptable for the frontend stack.
- If adding Playwright is too broad, add a lightweight integration harness with mocked fetch and DOM testing.
- Keep E2E minimal; this is smoke, not full UI test coverage.

Recommended files:

```text
frontend/package.json
frontend/playwright.config.*
frontend/tests/*
frontend/src/components/presentations/*
docs/*
```

## Hard boundaries

- Do not build a new design system.
- Do not rewrite existing inline styles.
- Do not change backend contracts.
- Do not require real LLM or real PPTX generation.
- Do not require real Postgres for frontend E2E.
- Do not test every visual detail.

## Acceptance criteria

- Frontend E2E or DOM smoke runs in CI/local command.
- Revision POST body is verified to omit `plan`.
- Existing Next build still passes.
- Backend tests remain green.

## Suggested validation

```bash
cd frontend
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e # if added

cd ..
python3 -m pytest -q
python3 -m compileall backend
```

---

# Issue P3 — Editable plan version timeline UI

## Goal

Expose presentation version lineage in frontend so operators can inspect older versions, not only latest metadata.

## Problem

O6 shows current/latest plan and latest diff, but users cannot browse the full version chain.

## Scope

Add a read-only version timeline UI.

Allowed work:

- Add backend endpoint if no suitable version-list endpoint exists.
- Add frontend API client for version listing.
- Show ordered versions for selected presentation.
- Show version number, parent, created time, change summary, file id.
- Allow selecting a version and loading its plan snapshot.
- Allow diffing selected version against parent if parent exists.

Recommended backend endpoints:

```text
GET /presentations/{presentation_id}/versions
```

Recommended frontend additions:

```text
VersionTimelinePanel
Version selector
Load selected plan
Load selected diff
```

## Hard boundaries

- No rollback in P3.
- No mutation UI.
- No arbitrary pairwise diff unless explicitly scoped.
- No PPTX preview/rendering.
- No plan editing.
- Preserve O6 current/latest inspector behavior.

## Acceptance criteria

- Users can see version lineage.
- Users can inspect a selected version plan.
- Users can inspect selected-version-vs-parent diff when parent exists.
- Access remains session/owner scoped.
- Safe schemas do not expose storage internals.

---

# Issue P4 — Revision preview and rollback

## Goal

Add controlled rollback/restore behavior for presentation versions.

## Problem

O7 can create revisions but cannot revert to an earlier accepted version.

## Scope

Backend first, frontend second if manageable:

- Add service operation to restore current presentation pointer to an existing version.
- Persist a new version or explicit restore event according to the repository model.
- Add API endpoint for rollback/restore.
- Add frontend action in version timeline.
- Require confirmation text or deliberate UI action.

Potential endpoint:

```text
POST /presentations/{presentation_id}/versions/{version_id}/restore
```

## Hard boundaries

- Do not delete existing versions.
- Do not mutate historical version rows.
- Do not overwrite stored files.
- Do not implement arbitrary branching DAG editing unless already supported.
- Do not add collaborative conflict resolution.
- Do not bypass ownership checks.

## Acceptance criteria

- Restore action changes current file/version safely.
- Historical lineage remains inspectable.
- Tests cover owner scoping and invalid version ids.
- Frontend refreshes metadata after restore.
- Operator can tell which version is current.

---

# Issue P5 — Dependency and security hardening

## Goal

Address dependency risk surfaced during O phase, especially frontend dependency warnings.

## Problem

`npm ci` reported a warning for `next@14.2.5`. O phase intentionally did not upgrade dependency stack.

## Scope

- Review frontend dependency versions.
- Upgrade Next.js to a patched compatible version if feasible.
- Keep React/Next major behavior stable unless unavoidable.
- Run `npm audit` and document accepted residuals.
- Update lockfile intentionally.
- Ensure build remains green.

Recommended files:

```text
frontend/package.json
frontend/package-lock.json
docs/*
```

## Hard boundaries

- Do not combine dependency upgrades with UI feature work.
- Do not migrate framework major versions unless a security fix requires it.
- Do not touch backend dependencies unless separately justified.
- Do not silence audit warnings without a documented reason.

## Acceptance criteria

- `npm ci` succeeds.
- `NEXT_TELEMETRY_DISABLED=1 npm run build` passes.
- Dependency changes are documented.
- Any remaining audit findings are documented with severity and rationale.

---

# Issue P6 — Deployment packaging

## Goal

Make the project easier to run consistently outside a developer shell.

## Scope

Add deployment packaging that may include:

- Dockerfile(s) if missing or incomplete.
- Compose file for backend + frontend + optional Postgres.
- `.env.example` with safe placeholders.
- storage volume layout.
- healthcheck wiring.
- operator commands for startup/shutdown.
- docs for local production-like run.

## Hard boundaries

- Do not bake secrets into images.
- Do not require proprietary external services to start the stack.
- Do not remove existing local dev workflows.
- Do not convert all tests to container-only.
- Do not add Kubernetes yet unless separately scoped.

## Acceptance criteria

- A clean operator can start a local stack from docs.
- `/health` and `/ready` behavior is documented.
- frontend can reach backend via documented env variable.
- storage directories/volumes are explicit.
- smoke script works against the running stack.

---

# Issue P7 — Auth and user-boundary hardening

## Goal

Strengthen session/presentation/revision access boundaries before multi-user deployment.

## Problem

The project currently uses local/dev-style user context in many tests. The presentation API has owner scoping, but it needs systematic hardening.

## Scope

- Audit all presentation/revision/plan endpoints for owner/session scoping.
- Add negative tests for cross-user access.
- Ensure frontend does not rely on hardcoded user identity.
- Add documentation describing current auth assumptions.
- Add TODO boundary for real auth integration if not in scope.

## Hard boundaries

- Do not implement full OAuth/SAML/auth provider in this issue.
- Do not introduce a user database unless already planned.
- Do not break local default-user development mode.
- Do not weaken existing tests.

## Acceptance criteria

- Cross-user tests exist for presentation list/get/plan/diff/revision/restore if restore exists.
- API returns 404/403 consistently according to existing convention.
- Docs state current auth boundary honestly.

---

# Issue P8 — Observability and release audit

## Goal

Create final release audit tooling for editable deck workflows.

## Scope

- Add a phase integrity/audit script for P phase.
- Include branch/history checks.
- Include required file presence.
- Include focused regression list.
- Include frontend build check.
- Include optional operator smoke.
- Include safe output without secrets.

## Hard boundaries

- Do not require network services by default.
- Do not duplicate all CI logic if a CI workflow already covers it.
- Do not print secrets.
- Do not mutate repo state.

## Acceptance criteria

- One command can summarize P phase readiness.
- It catches missing key files.
- It runs focused tests.
- It can optionally run full suite/build/smoke.
- It exits nonzero on failed checks.

---

# Recommended P phase order

```text
P1 Real Postgres CI gate
P2 Frontend E2E deck revision smoke
P3 Editable plan version timeline UI
P4 Revision preview and rollback
P5 Dependency and security hardening
P6 Deployment packaging
P7 Auth and user-boundary hardening
P8 Observability and release audit
```

If time is limited, do this minimum subset:

```text
P1, P2, P5, P8
```

If product UX is the priority:

```text
P2, P3, P4
```

If deployment readiness is the priority:

```text
P1, P5, P6, P8
```
