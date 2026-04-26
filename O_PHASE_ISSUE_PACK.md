# O_PHASE_ISSUE_PACK.md

## Phase O — Editable deck productization and deployment hardening

Phase O starts after the accepted M/N slides backend foundation.

Accepted baseline:
- M9-M15 accepted the slides generation, image/media pipeline, structured blocks, source grounding, and deck revision service foundation.
- N1 accepted presentation retrieval API.
- N2 accepted deck revision API with explicit plan payload.
- N3 accepted revision persistence integration tests.
- N4 accepted revision strategy boundary with deterministic and provider-backed strategy.
- N5 accepted sample deck export and optional visual smoke validation.
- N6 accepted public slides API schema stabilization.
- N7 accepted operational regression pack and review tactics.

Phase O turns the accepted backend mechanics into a productizable editable deck workflow and prepares safer deployment/CI hardening. It must preserve the M/N foundation rather than re-litigating it.

---

## Global O phase goals

1. Persist editable presentation plan snapshots so deck revisions no longer require clients to submit the entire plan.
2. Make revision APIs product-ready while preserving existing explicit-plan compatibility where needed.
3. Prove persistence across SQLite and Postgres paths honestly.
4. Add frontend UI in a controlled, staged way after backend contracts are stable.
5. Harden visual smoke/CI and deployment checks without requiring public internet access.
6. Improve lifecycle, quota, cleanup, observability, and operator docs.
7. Keep all accepted M/N regression gates green.

---

## Global O phase non-goals

Do not use Phase O to:

- rewrite the slides subsystem from scratch;
- replace the composition root;
- replace the accepted artifact/storage/repository model;
- make SQLite a production truth layer;
- store binary PPTX files primarily in metadata databases;
- add route-local service wiring;
- add fake success paths for missing plans, missing sources, storage failures, or provider failures;
- silently fall back from provider-backed revision to deterministic revision in production;
- expose `storage_key`, `storage_uri`, local filesystem paths, or provider secrets in public APIs;
- require public-internet deployment assumptions;
- implement multiple O issues in one patch;
- weaken or delete M/N regression tests to make new code pass.

---

## Required O phase regression gates

Every O issue that touches backend code must run:

```bash
python3 -m pytest -q
python3 -m compileall backend
```

Slides-specific changes must also consider:

```bash
python3 -m pytest backend/tests/api/test_n7_slides_product_regression.py -q
python3 -m pytest backend/tests/api/test_n6_slides_api_schema_stabilization.py -q
python3 -m pytest backend/tests/api/test_n2_deck_revision_api.py -q
python3 -m pytest backend/tests/integrations/test_n3_revision_persistence.py -q
python3 -m pytest backend/tests/smoke/test_n5_sample_deck_export.py -q
```

Frontend issues must run the accepted frontend checks from the repository, such as lint/build, after inspecting the live frontend package scripts.

---

# O1 — Persist editable PresentationPlan snapshots

## Problem

N2 revision APIs currently require an explicit `plan` payload because no accepted persistent editable plan snapshot exists. This is honest but not product-ready.

## Scope

Add a durable metadata representation for editable deck plans tied to presentations and presentation versions.

## Allowed changes

- Domain model for `PresentationPlanSnapshot` or equivalent.
- Repository protocol for plan snapshots.
- SQLite implementation.
- Postgres implementation only if current migration/bootstrap style supports it honestly.
- Composition root wiring.
- Service methods to create/read latest plan snapshot.
- Tests proving persistence and ownership/session boundaries.

## Hard boundaries

- Do not change N2 revision API behavior yet. That belongs to O2.
- Do not build frontend UI.
- Do not store binary PPTX in the plan snapshot.
- Do not fake snapshots from generated PPTX bytes.
- Do not silently create snapshots during retrieval routes unless generation/revision flow explicitly writes one.

## Acceptance criteria

- A presentation can have one or more plan snapshots.
- A snapshot is tied to a presentation and optionally a presentation version.
- Latest snapshot can be loaded deterministically.
- Snapshot JSON round-trips `PresentationPlan` without losing slide ids, slide types, story stages, bullets, notes, layout hints, blocks, media references, and source grounding metadata where currently represented.
- Existing N1-N7 tests stay green.

---

# O2 — Revision API without explicit plan payload

## Problem

N2 accepted explicit-plan revision requests. Product revision should be possible by presentation id + target slide/stage when a persisted plan snapshot exists.

## Scope

Add plan-loading revision API path using O1 snapshots while preserving explicit-plan compatibility.

## Allowed changes

- Request schemas that allow omitting `plan` when a current plan snapshot exists.
- Revision route/service loading latest plan snapshot.
- Persist revised plan snapshot after successful revision.
- Error response for missing plan snapshot.
- Tests for no-plan revision, explicit-plan compatibility, missing snapshot failure, lineage, and current file advance.

## Hard boundaries

- Do not invent a plan if no snapshot exists.
- Do not infer editable plan from PPTX XML.
- Do not add semantic provider production switch. That belongs to O10.
- Do not add frontend UI.

## Acceptance criteria

- `POST /presentations/{id}/revisions/slide` can work without `plan` if snapshot exists.
- `POST /presentations/{id}/revisions/section` can work without `plan` if snapshot exists.
- Existing explicit `plan` request remains supported.
- Successful revision creates new `StoredFile`, `PresentationVersion`, and plan snapshot.
- Missing plan snapshot returns a clear 400/409, not fake success.

---

# O3 — Plan snapshot retrieval, diff, and inspectability API

## Problem

Once plan snapshots exist, users and debugging tools need safe metadata endpoints to inspect current plan and revision differences.

## Scope

Expose safe plan snapshot retrieval and revision diff metadata.

## Allowed changes

- `GET /presentations/{id}/plan` for current safe plan snapshot.
- `GET /presentations/{id}/versions/{version_id}/plan` if backed by repository.
- `GET /presentations/{id}/revisions/{version_id}/diff` for safe slide-level deltas if available.
- Explicit schemas hiding storage internals.
- Tests for auth, missing plan, version-specific plan, and safe schema.

## Hard boundaries

- Do not expose raw storage keys or local paths.
- Do not expose provider prompts/secrets.
- Do not compute deep semantic diffs with LLM.
- Do not build frontend UI.

## Acceptance criteria

- Current plan can be retrieved safely.
- Version plan can be retrieved where snapshot exists.
- Diff endpoint reports slide ids/titles/bullet deltas using accepted revision delta data or deterministic structural comparison.
- Unauthorized access fails clearly.

---

# O4 — Postgres revision and plan persistence integration

## Problem

N3 proved SQLite + local storage durability. Production-facing confidence requires Postgres-backed metadata path coverage.

## Scope

Add honest Postgres integration tests for presentation versions and plan snapshots where test infrastructure supports it.

## Allowed changes

- Postgres integration tests using existing Postgres test harness.
- Minimal repository fixes required by tests.
- Bootstrap/migration alignment if existing project pattern requires it.
- Documentation of skipped Postgres tests when service is unavailable.

## Hard boundaries

- Do not fake Postgres with SQLite.
- Do not require external public internet.
- Do not make Postgres tests flaky or always-on when no test database exists.
- Do not redesign repositories.

## Acceptance criteria

- Postgres repositories persist and retrieve presentation versions.
- Postgres repositories persist and retrieve plan snapshots.
- Lineage ordering is proven.
- Test skip is explicit and honest if Postgres test DSN is absent.

---

# O5 — Frontend presentation registry UI

## Problem

Backend presentation retrieval exists, but users need a product UI to see generated presentations and open them.

## Scope

Add the first controlled frontend surface for presentation registry and metadata viewing.

## Allowed changes

- API client methods for N1 presentation endpoints.
- Presentation list component per session.
- Presentation detail card showing title, status, current file, latest version.
- Loading/error/empty states.
- Frontend tests or build/lint checks according to repository setup.

## Hard boundaries

- Do not implement revision editing UI. That belongs to O6/O7.
- Do not expose storage internals.
- Do not bypass backend auth/session model.
- Do not redesign the app shell.

## Acceptance criteria

- User can list presentations for a session.
- User can view presentation metadata.
- UI handles empty/missing/error states.
- Backend tests remain green.
- Frontend checks pass.

---

# O6 — Frontend deck revision UI contract

## Problem

Revision API exists but needs a safe UI contract before building rich editor interactions.

## Scope

Add frontend API client/types and minimal revision form flow without advanced editor features.

## Allowed changes

- API client for revision endpoints.
- Type definitions matching N2/O2 schemas.
- Minimal slide revision form: target slide index/id, instruction, submit.
- Minimal section revision form: stage, instruction, submit.
- Revision response display and lineage refresh.
- Tests/build/lint.

## Hard boundaries

- Do not build drag-and-drop editor.
- Do not implement live PPTX canvas editing.
- Do not add provider selection UI.
- Do not fake plan snapshots client-side.
- Do not hide backend errors.

## Acceptance criteria

- User can submit a slide revision from UI where backend supports it.
- User can submit a section revision from UI where backend supports it.
- UI displays error when plan snapshot is missing or request is invalid.
- Presentation metadata refreshes after revision.

---

# O7 — Editable deck outline editor MVP

## Problem

A product deck workflow needs controlled editing of the plan/outline before regeneration or revision.

## Scope

Add minimal safe outline editing UI backed by persisted plan snapshots.

## Allowed changes

- Backend endpoint for updating editable plan snapshot if O1/O3 established safe write model.
- Frontend outline editor for slide title, bullets, notes, stage, layout hint.
- Validation and save flow.
- Regenerate deck from edited plan only if existing service supports it honestly.

## Hard boundaries

- Do not build full PowerPoint-like editor.
- Do not edit binary PPTX directly.
- Do not allow arbitrary JSON plan injection without validation.
- Do not mutate historical snapshots in place unless explicitly modeled as draft state.

## Acceptance criteria

- User can edit slide titles/bullets/notes in current draft plan.
- Saved draft creates/updates an accepted draft snapshot model.
- Invalid plan edits fail clearly.
- Historical version snapshots remain inspectable.

---

# O8 — CI visual smoke profile

## Problem

N5 visual smoke was optional locally. CI should provide a controlled job/profile for PPTX visual conversion when LibreOffice is available.

## Scope

Add CI-compatible visual smoke profile without making local development brittle.

## Allowed changes

- Dedicated smoke marker or test profile.
- CI config for LibreOffice/headless conversion if project CI supports it.
- Clear skip behavior when binary is unavailable.
- Documentation for local install/run.

## Hard boundaries

- Do not make all developers install LibreOffice for normal tests.
- Do not commit converted PDFs/screenshots unless explicitly approved.
- Do not add public internet runtime dependency.
- Do not use OCR as primary validation.

## Acceptance criteria

- Normal `pytest -q` remains fast and stable.
- Visual smoke can run in a dedicated environment.
- Skips are explicit and honest.
- PPTX-to-PDF conversion failure fails the visual smoke job.

---

# O9 — Source grounding expansion with explicit capability boundaries

## Problem

Source-grounding exists for extracted/cached text. Product value improves with better handling of PDF/table/image-derived evidence, but unsupported extraction must not be faked.

## Scope

Expand source grounding only where extraction is already supported or can be added honestly behind explicit capability flags.

## Allowed changes

- Grounding metadata for document/table-derived fragments.
- Better source labels and citation grouping.
- Explicit unsupported-source errors.
- Tests for supported/unsupported paths.

## Hard boundaries

- Do not claim OCR/visual grounding unless implemented and tested.
- Do not use OCR repeatedly or as a hidden default.
- Do not add public internet extraction services.
- Do not invent citations from prompt text without source refs.

## Acceptance criteria

- Supported sources generate typed citations.
- Unsupported sources fail or degrade explicitly.
- Public API remains safe and storage-internal-free.
- Existing N6/N7 schema tests remain green.

---

# O10 — Storage lifecycle, quota, and cleanup

## Problem

Revision flows create new files and versions. Product deployment needs lifecycle rules to avoid unbounded storage growth.

## Scope

Add storage lifecycle primitives and safe cleanup operations for generated decks/revisions.

## Allowed changes

- Repository queries for orphaned/unreferenced artifacts if needed.
- Service-level cleanup for superseded temporary files.
- Quota metadata and checks if current domain supports it.
- Admin/maintenance command or internal service method.
- Tests proving active versions are not deleted.

## Hard boundaries

- Do not delete current presentation files.
- Do not delete files referenced by any active artifact/version/source.
- Do not expose destructive public endpoints without explicit approval.
- Do not run cleanup automatically at import/startup.

## Acceptance criteria

- Cleanup identifies safe candidates.
- Active current files and lineage files are preserved.
- Dry-run mode exists for destructive operations.
- Tests cover no-delete cases and cleanup cases.

---

# O11 — Provider-backed revision production configuration and observability

## Problem

N4 introduced provider-backed strategy boundary. Production needs explicit configuration, logging, and failure visibility.

## Scope

Make semantic revision strategy selectable through accepted configuration and observable without silent fallback.

## Allowed changes

- Config option for revision strategy mode: deterministic/provider.
- Composition-root wiring to select strategy.
- Structured logs/metrics around revision strategy execution.
- Provider failure surfaces to API clearly.
- Tests for deterministic mode, provider mode with fake provider, and provider failure.

## Hard boundaries

- Do not silently fallback from provider to deterministic in production.
- Do not log prompts with sensitive source text unless policy allows and redaction exists.
- Do not expose provider keys.
- Do not add unsupported providers.

## Acceptance criteria

- Deterministic mode remains default for offline/test profile.
- Provider mode uses accepted text provider service.
- Provider failures fail honestly and are observable.
- No secrets leak in logs/errors.

---

# O12 — Deployment hardening and operator runbook

## Problem

The slides subsystem now has storage, queues, revisions, plan snapshots, optional visual smoke, and provider-backed strategies. Operators need a safe deployment/runbook contract.

## Scope

Document and test deployment requirements for the accepted backend profile.

## Allowed changes

- Deployment/runbook docs.
- Environment variable documentation.
- Health/smoke checklist.
- Docker/compose notes if already present in project.
- Backend smoke command script only if it is simple and offline-safe.

## Hard boundaries

- Do not introduce a new deployment platform.
- Do not require public internet.
- Do not hardcode local machine paths.
- Do not store secrets in docs or code.
- Do not change runtime behavior merely for docs.

## Acceptance criteria

- Operator can run backend tests/smoke from documented commands.
- Required env vars are listed.
- Optional LibreOffice visual smoke is documented.
- Failure triage for storage/repository/provider/revision paths is documented.

---

## Recommended O phase sequence

1. O1 — Persist editable PresentationPlan snapshots
2. O2 — Revision API without explicit plan payload
3. O3 — Plan snapshot retrieval, diff, and inspectability API
4. O4 — Postgres revision and plan persistence integration
5. O5 — Frontend presentation registry UI
6. O6 — Frontend deck revision UI contract
7. O7 — Editable deck outline editor MVP
8. O8 — CI visual smoke profile
9. O9 — Source grounding expansion with explicit capability boundaries
10. O10 — Storage lifecycle, quota, and cleanup
11. O11 — Provider-backed revision production configuration and observability
12. O12 — Deployment hardening and operator runbook

Do not compress these into a single mega-patch. Each issue must be independently reviewable and revertible.
