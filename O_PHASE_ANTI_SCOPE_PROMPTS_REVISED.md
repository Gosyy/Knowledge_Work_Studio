# O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md

This file contains self-contained Codex prompts for Phase O.
Each prompt is copy-paste ready and explicitly reads `O_PHASE_ISSUE_PACK.md`.

---

# Global O phase Codex contract

```text
Work from the repository root.

This is not a greenfield project.
F-M8, M9-M15, N1-N7, and N_REVIEW_TACTICS.md are accepted.
Do not re-litigate accepted architecture.
Do not replace the composition root, official execution coordinator, storage model, repository model, provider model, deployment profile, source extraction model, slides planning model, layout/template engine, media foundation, image pipeline, structured slide blocks, source-aware grounding model, deck revision service, presentation retrieval API, revision API, revision strategy boundary, public slides API schemas, or N7 regression pack unless the current O issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F-N architecture was preserved.
5. List commands run.
6. Report test results.

Required checks for backend changes:
- python3 -m pytest -q
- python3 -m compileall backend

Required checks for frontend changes:
- Inspect live package scripts first.
- Run the accepted lint/build/test commands available in the repository.
- If a frontend command is unavailable, report it honestly and do not fake success.

Stop conditions:
- If completing the issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
- If a change would expose unsafe storage internals or provider secrets, stop.
```

---

# Global O phase anti-scope rules

```text
Do NOT:
- Redesign accepted F-N architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres or SQLite metadata tables.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Weaken N7 regression coverage.
- Expose `storage_key`, `storage_uri`, local filesystem paths, internal storage keys, provider prompts, provider keys, or secrets through public APIs.
- Silently fallback from provider-backed logic to deterministic/fake behavior in production.
- Touch frontend unless the current O issue explicitly allows frontend changes.
- Implement multiple O issues in one run.
```

---

# Global O phase review gate

```text
Review dimensions:
1. Scope discipline
2. Architecture preservation
3. Truth-layer correctness
4. Public API safety
5. Persistence durability
6. Revision lineage correctness
7. Source-grounding honesty
8. Provider failure honesty
9. Test coverage
10. Operational hygiene
11. Backward compatibility
12. Product contract clarity

Reject if:
- adjacent issue work was implemented
- accepted architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into the offline/intranet profile
- unsafe storage details are exposed accidentally
- binary artifacts are stored in metadata repositories
- python3 pytest or compileall fails
```

---

# Prompt O1 — Persist editable PresentationPlan snapshots

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- N_REVIEW_TACTICS.md
- backend/app/services/slides_service/outline.py
- backend/app/services/slides_service/blocks.py
- backend/app/services/slides_service/source_grounding.py
- backend/app/services/slides_service/revision.py
- backend/app/domain/metadata/models.py
- backend/app/domain/models.py
- backend/app/repositories/interfaces.py
- backend/app/repositories/sqlite.py
- backend/app/repositories/postgres.py
- backend/app/repositories/__init__.py
- backend/app/composition.py
- backend/tests/integrations/
- backend/tests/services/test_m15_deck_revision.py
- backend/tests/api/test_n7_slides_product_regression.py

Implement O1 only.

Issue scope:
Add durable editable PresentationPlan snapshots tied to presentations and versions.

Allowed changes:
- domain model for presentation plan snapshots
- repository protocol for plan snapshots
- SQLite repository implementation
- Postgres repository implementation only if current repository/bootstrap pattern supports it honestly
- composition root wiring
- service methods to create/read latest snapshot
- tests proving JSON round-trip, latest lookup, and ownership/session boundaries where applicable

Adjacent issue firewall:
- O1 must NOT change revision APIs to omit plan. That belongs to O2.
- O1 must NOT add plan retrieval API. That belongs to O3.
- O1 must NOT add frontend UI. That belongs to O5-O7.
- O1 must NOT add Postgres integration test harness beyond minimal repository support. That belongs to O4.

Hard anti-scope:
- Do NOT store binary PPTX bytes in plan snapshots.
- Do NOT infer plan snapshots from existing PPTX XML.
- Do NOT silently create fake snapshots when none exist.
- Do NOT mutate historical version snapshots in place.
- Do NOT drop blocks/media/source-grounding fields if they are present in the current plan model.

Acceptance criteria:
- A presentation can have multiple plan snapshots.
- Latest snapshot can be loaded deterministically.
- Snapshot can be tied to a PresentationVersion.
- PresentationPlan round-trips without losing accepted fields.
- Existing M/N tests remain green.

Required tests:
- create/read plan snapshot
- latest snapshot ordering
- round-trip plan with blocks/source grounding/media-safe metadata where represented
- missing snapshot behavior
- SQLite durability across repository re-creation
```

---

# Prompt O2 — Revision API without explicit plan payload

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- N_REVIEW_TACTICS.md
- backend/app/api/routes/revisions.py
- backend/app/api/schemas/revisions.py
- backend/app/services/slides_service/revision.py
- backend/app/services/presentation_catalog_service.py
- backend/app/composition.py
- backend/tests/api/test_n2_deck_revision_api.py
- backend/tests/api/test_n7_slides_product_regression.py
- O1 files introduced for plan snapshots

Implement O2 only.

Issue scope:
Allow revision APIs to load the latest persisted plan snapshot when request omits explicit `plan`.

Allowed changes:
- request schema update making `plan` optional only where snapshot loading exists
- service/route logic to load current plan snapshot
- persist revised plan snapshot after successful revision
- tests for no-plan revision and explicit-plan compatibility

Adjacent issue firewall:
- O2 must NOT add plan retrieval/diff APIs. That belongs to O3.
- O2 must NOT add frontend UI.
- O2 must NOT add provider production config. That belongs to O11.
- O2 must NOT expand source grounding. That belongs to O9.

Hard anti-scope:
- Do NOT invent a plan if snapshot is missing.
- Do NOT parse PPTX to recover a plan.
- Do NOT silently fall back to explicit-plan-only behavior when no plan is supplied.
- Do NOT mutate old snapshots.

Acceptance criteria:
- Slide revision works without `plan` when current snapshot exists.
- Section revision works without `plan` when current snapshot exists.
- Explicit `plan` request remains supported.
- Successful revision persists new plan snapshot linked to new version.
- Missing snapshot returns clear client error.
```

---

# Prompt O3 — Plan snapshot retrieval, diff, and inspectability API

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- N_REVIEW_TACTICS.md
- backend/app/api/routes/presentations.py
- backend/app/api/routes/revisions.py
- backend/app/api/schemas/presentations.py
- backend/app/api/schemas/revisions.py
- backend/app/api/schemas/slides.py
- O1/O2 plan snapshot service/repository files
- backend/tests/api/

Implement O3 only.

Issue scope:
Expose safe plan snapshot retrieval and version/diff inspectability.

Allowed changes:
- safe plan snapshot response schemas
- current plan endpoint
- version-specific plan endpoint if backed by repository
- structural diff endpoint or safe diff schema using existing revision delta data
- API tests for auth, missing plan, safe schema, and version lookup

Adjacent issue firewall:
- O3 must NOT build frontend UI.
- O3 must NOT create or revise plans.
- O3 must NOT add semantic/LLM diffing.
- O3 must NOT alter storage lifecycle.

Hard anti-scope:
- Do NOT expose raw storage keys/URIs/local paths.
- Do NOT expose provider prompts or secrets.
- Do NOT return internal dataclass `__dict__` as public contract.
- Do NOT fake diffs when no comparable snapshots exist.

Acceptance criteria:
- Current plan can be retrieved in a stable public schema.
- Version plan can be retrieved where snapshot exists.
- Missing plan/version fails clearly.
- Diff response is structural, safe, and typed.
```

---

# Prompt O4 — Postgres revision and plan persistence integration

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/repositories/postgres.py
- backend/app/repositories/interfaces.py
- backend/app/domain/metadata/models.py
- backend/tests/integrations/
- existing Postgres test fixtures/config
- O1-O3 files

Implement O4 only.

Issue scope:
Prove Postgres-backed persistence for presentation versions and plan snapshots honestly.

Allowed changes:
- Postgres integration tests using existing test DSN/harness
- minimal repository fixes required by the tests
- explicit skip if Postgres test DSN is absent
- docs/comments explaining required env var if already consistent with project style

Adjacent issue firewall:
- O4 must NOT redesign repositories.
- O4 must NOT change API behavior.
- O4 must NOT build frontend UI.
- O4 must NOT make SQLite production truth.

Hard anti-scope:
- Do NOT fake Postgres with SQLite.
- Do NOT require public internet.
- Do NOT make all local test runs require Postgres unless project already does.
- Do NOT hide migration/bootstrap mismatch.

Acceptance criteria:
- Postgres persists PresentationVersion lineage.
- Postgres persists plan snapshots.
- Ordering/latest lookup is proven.
- Skip is explicit and honest when Postgres is unavailable.
```

---

# Prompt O5 — Frontend presentation registry UI

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- frontend package/config files
- existing frontend API client patterns
- existing session/task/artifact UI patterns
- backend/app/api/routes/presentations.py
- backend/app/api/schemas/presentations.py

Implement O5 only.

Issue scope:
Add frontend presentation registry and metadata viewing using accepted N1 endpoints.

Allowed changes:
- frontend API client for presentation list/get
- types matching public presentation schema
- presentation list per session
- presentation detail card
- loading/error/empty states
- frontend tests or lint/build updates according to live project setup

Adjacent issue firewall:
- O5 must NOT add revision UI. That belongs to O6.
- O5 must NOT add outline editor. That belongs to O7.
- O5 must NOT change backend API unless a tiny compatibility fix is absolutely required.

Hard anti-scope:
- Do NOT expose storage_key/storage_uri/local paths.
- Do NOT bypass backend auth/session checks.
- Do NOT add a new frontend framework.
- Do NOT move business logic into UI components.

Acceptance criteria:
- User can list presentations for a session.
- User can view selected presentation metadata.
- Empty/error/loading states are handled.
- Backend tests remain green.
- Frontend lint/build checks pass or unavailable commands are reported honestly.
```

---

# Prompt O6 — Frontend deck revision UI contract

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- frontend API client/types/components
- backend/app/api/routes/revisions.py
- backend/app/api/schemas/revisions.py
- O5 presentation UI files

Implement O6 only.

Issue scope:
Add minimal frontend revision submit flow using accepted revision API.

Allowed changes:
- frontend API client for revision endpoints
- request/response types
- minimal slide revision form
- minimal section revision form
- revision response display
- lineage refresh/display if already accessible
- tests/lint/build

Adjacent issue firewall:
- O6 must NOT build rich outline editor. That belongs to O7.
- O6 must NOT add provider selection UI. That belongs to later product decision.
- O6 must NOT fake missing plan snapshots client-side.
- O6 must NOT hide backend errors.

Hard anti-scope:
- Do NOT directly edit PPTX binary.
- Do NOT parse PPTX in frontend.
- Do NOT implement drag-and-drop deck editor.
- Do NOT bypass backend schemas.

Acceptance criteria:
- User can submit slide revision.
- User can submit section revision.
- UI shows success and backend error states honestly.
- Presentation metadata/lineage refreshes after revision.
```

---

# Prompt O7 — Editable deck outline editor MVP

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- O1-O3 backend plan snapshot files
- O5/O6 frontend files
- backend/app/services/slides_service/outline.py
- backend/app/api/schemas/slides.py

Implement O7 only.

Issue scope:
Add minimal editable deck outline editor backed by persisted plan snapshots.

Allowed changes:
- safe backend endpoint for updating current draft snapshot if O1/O3 established write model
- frontend editor for title, bullets, notes, stage, layout hint
- validation and save flow
- tests for valid/invalid plan edits

Adjacent issue firewall:
- O7 must NOT build PowerPoint-like canvas editor.
- O7 must NOT add live slide rendering editor.
- O7 must NOT implement storage cleanup.
- O7 must NOT add CI visual smoke.

Hard anti-scope:
- Do NOT mutate historical version snapshots in place.
- Do NOT accept arbitrary unvalidated JSON.
- Do NOT drop structured blocks/media/source metadata accidentally.
- Do NOT edit binary PPTX directly.

Acceptance criteria:
- User can edit current draft plan outline fields.
- Invalid edits fail clearly.
- Historical snapshots remain immutable.
- Saved draft is durable and inspectable.
```

---

# Prompt O8 — CI visual smoke profile

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/tests/smoke/test_n5_sample_deck_export.py
- project CI config files
- README/deployment docs if present

Implement O8 only.

Issue scope:
Add a CI/local profile for optional PPTX visual smoke using LibreOffice/headless conversion.

Allowed changes:
- pytest marker/profile for visual smoke
- CI config update if project CI exists and supports LibreOffice setup
- local run documentation
- explicit skip behavior if binary is missing

Adjacent issue firewall:
- O8 must NOT add OCR validation.
- O8 must NOT add frontend preview.
- O8 must NOT commit generated PDFs/images unless explicitly approved.
- O8 must NOT require LibreOffice for normal unit test runs.

Hard anti-scope:
- Do NOT make `python3 -m pytest -q` flaky because LibreOffice is missing.
- Do NOT claim visual smoke passed when conversion failed.
- Do NOT require public internet at runtime.

Acceptance criteria:
- Normal backend tests remain fast/stable.
- Dedicated visual smoke command/job exists.
- Missing LibreOffice skip is explicit.
- Conversion failure fails dedicated visual smoke.
```

---

# Prompt O9 — Source grounding expansion with explicit capability boundaries

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/source_extraction.py
- backend/app/services/task_source_service.py
- backend/app/services/slides_service/source_grounding.py
- backend/app/api/schemas/slides.py
- backend/tests/api/test_n6_slides_api_schema_stabilization.py
- backend/tests/api/test_n7_slides_product_regression.py

Implement O9 only.

Issue scope:
Expand source grounding only for honestly supported extracted/derived content paths.

Allowed changes:
- better citation grouping/labels
- table/document-derived fragment metadata if already extractable
- explicit unsupported-source errors or safe degradation
- schema/test updates for supported paths

Adjacent issue firewall:
- O9 must NOT add plan snapshot features.
- O9 must NOT add frontend.
- O9 must NOT add storage cleanup.
- O9 must NOT add OCR/visual grounding unless fully implemented and tested.

Hard anti-scope:
- Do NOT fake OCR or visual grounding.
- Do NOT invent citations from non-source prompt text.
- Do NOT add public internet extraction services.
- Do NOT run repeated OCR by default.
- Do NOT leak storage internals.

Acceptance criteria:
- Supported sources produce typed citations.
- Unsupported sources fail/degrade explicitly.
- Public schema remains safe.
- N6/N7 regression remains green.
```

---

# Prompt O10 — Storage lifecycle, quota, and cleanup

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/integrations/file_storage/
- backend/app/services/artifact_service/
- backend/app/services/slides_service/revision.py
- backend/app/repositories/interfaces.py
- backend/app/repositories/sqlite.py
- backend/app/repositories/postgres.py
- tests around artifacts/stored files/presentations

Implement O10 only.

Issue scope:
Add safe lifecycle/cleanup primitives for generated decks and revisions.

Allowed changes:
- internal cleanup service or maintenance command
- dry-run mode
- repository queries for safe candidates if required
- tests ensuring active/current/versioned files are preserved

Adjacent issue firewall:
- O10 must NOT expose destructive public endpoint unless explicitly approved.
- O10 must NOT add frontend.
- O10 must NOT change revision semantics.
- O10 must NOT add provider config.

Hard anti-scope:
- Do NOT delete current presentation files.
- Do NOT delete files referenced by active artifact/version/source records.
- Do NOT run cleanup at import/startup.
- Do NOT perform destructive cleanup without dry-run support.

Acceptance criteria:
- Cleanup candidates are identified safely.
- Dry-run reports candidates without deletion.
- Active lineage files are preserved.
- Tests cover both cleanup and no-delete cases.
```

---

# Prompt O11 — Provider-backed revision production configuration and observability

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/core/config.py
- backend/app/composition.py
- backend/app/services/llm_text_service.py
- backend/app/services/slides_service/revision_strategy.py
- backend/app/services/slides_service/revision.py
- backend/tests/services/test_n4_revision_strategy.py

Implement O11 only.

Issue scope:
Make revision strategy mode configurable and observable without silent fallback.

Allowed changes:
- config option for revision strategy mode
- composition-root strategy selection
- structured logging/metrics where project style supports it
- tests for deterministic mode, provider mode with fake provider, provider failure

Adjacent issue firewall:
- O11 must NOT add new provider implementations.
- O11 must NOT add provider selection UI.
- O11 must NOT change public revision API shape unless necessary for clear errors.
- O11 must NOT add public internet requirements.

Hard anti-scope:
- Do NOT silently fallback from provider to deterministic in production.
- Do NOT log secrets/provider keys.
- Do NOT log full source text/prompts unless redaction policy exists.
- Do NOT fake provider success.

Acceptance criteria:
- Deterministic mode remains safe default for offline/test profile.
- Provider mode uses accepted LLMTextService path.
- Provider failure surfaces clearly.
- Tests prove no silent fallback.
```

---

# Prompt O12 — Deployment hardening and operator runbook

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- O_PHASE_ISSUE_PACK.md
- O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- README.md
- docs/ if present
- docker-compose files if present
- backend/app/core/config.py
- N_REVIEW_TACTICS.md

Implement O12 only.

Issue scope:
Document and harden operator runbook for accepted backend/slides profile.

Allowed changes:
- deployment/runbook documentation
- environment variable table
- smoke checklist
- troubleshooting guide for storage/repository/provider/revision paths
- simple offline-safe smoke command if consistent with project style

Adjacent issue firewall:
- O12 must NOT introduce a new deployment platform.
- O12 must NOT change product behavior unless a tiny docs-linked smoke helper is explicitly required.
- O12 must NOT add frontend product features.

Hard anti-scope:
- Do NOT require public internet.
- Do NOT hardcode local machine paths.
- Do NOT include secrets.
- Do NOT claim unsupported deployment modes are supported.
- Do NOT change runtime behavior merely for docs.

Acceptance criteria:
- Operator can run documented backend checks.
- Required and optional env vars are documented.
- Optional LibreOffice visual smoke is documented.
- Failure triage covers storage, repository, provider, source grounding, and revision paths.
```
