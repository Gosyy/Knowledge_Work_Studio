# N_PHASE_ISSUE_PACK.md

## Purpose

This pack defines the post-M15 slides productization and hardening roadmap.

Accepted baseline before this pack:
- F-M8 phases are accepted.
- M9-M15 slides subsystem phases are accepted.
- Current slides generation has typed planning, layout/templates, PPTX media embedding, image pipeline, structured slide blocks, source-aware grounding, and a service-level deck revision flow.
- Current revision support exists at backend service level; it is not yet a stable public API/editor contract.

This phase turns the accepted M9-M15 subsystem into a product-facing, API-stable, revision-capable presentation workflow.

## Required implementation order

1. N1 — Presentation artifact registry and retrieval API
2. N2 — Deck revision API contract
3. N3 — Revision persistence integration tests
4. N4 — Provider-backed semantic revision strategy
5. N5 — Sample deck export and visual smoke validation
6. N6 — Slides API schema stabilization
7. N7 — Operational hardening and regression pack

Do not reorder these issues unless an explicit later architecture decision says so.

---

## Cross-issue architectural rules

- Do not redesign accepted F-M15 architecture.
- Do not replace the composition root with route-local wiring.
- Do not reintroduce transitional orchestration surfaces.
- Do not make SQLite a production truth layer.
- Do not store binary files primarily in Postgres.
- Do not activate non-GigaChat providers in the approved deployment profile.
- Do not add public-internet deployment assumptions.
- Do not add fake success paths.
- Do not hide missing infrastructure behind local fallback.
- Do not remove tests merely to make the suite pass.
- Do not touch frontend unless the issue explicitly allows it.
- Do not implement multiple N issues in one run.
- Preserve existing M9-M15 behavior unless the current issue explicitly requires a backward-compatible extension.
- Use existing repository/storage/provider abstractions instead of new ad hoc infrastructure.

---

## Cross-issue review dimensions

Every N-phase issue must be reviewed on:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene
7. Backward compatibility
8. Product contract clarity

Reject if:
- Adjacent issue work was implemented.
- Accepted architecture was changed without explicit scope.
- Tests were removed without stricter replacement.
- Production config silently falls back to local/fake behavior.
- Fake implementation claims real capability.
- Frontend was changed outside scope.
- Public-internet dependency was introduced into the offline intranet profile.
- Existing M9-M15 flows regress.
- API schemas leak unsafe internal storage details.
- `python3 -m pytest -q` or `python3 -m compileall backend` fails.

---

# N1 — Presentation artifact registry and retrieval API

## Goal

Expose generated presentations as first-class retrievable backend entities, not only task artifacts.

## Current problem

The slides subsystem can create PPTX artifacts and M15 can revise presentations through a service, but the product-facing retrieval contract is still weak:
- generated presentations are not consistently discoverable through a dedicated API surface;
- clients do not have a stable presentation metadata schema;
- current presentation file/version references are not exposed in a clear, safe shape;
- existing task result metadata is not enough for product workflows.

## Scope

Add a backend retrieval surface for presentation metadata.

Allowed changes:
- Presentation response schemas.
- Routes for listing presentations by session.
- Route for retrieving one presentation metadata record.
- Safe exposure of current file reference.
- Optional version summary if already backed by existing repositories.
- Dependency wiring through the accepted composition root.
- Focused API tests with SQLite test backend.

## Minimum API shape

- `GET /sessions/{session_id}/presentations`
- `GET /presentations/{presentation_id}`

Response must be stable and safe:
- presentation id
- session id
- title
- presentation type
- status
- current file id or current file metadata reference
- created/updated timestamps
- optional current version number if available without inventing lineage

## Likely files

- `backend/app/api/routes/` presentation route file or existing route module if already appropriate
- `backend/app/api/schemas/`
- `backend/app/api/dependencies.py`
- `backend/app/composition.py`
- `backend/tests/api/`

## Adjacent issue firewall

- N1 must NOT add deck revision endpoints. That belongs to N2.
- N1 must NOT add provider-backed semantic revision. That belongs to N4.
- N1 must NOT add frontend editor UI.
- N1 must NOT redesign M15 revision service.
- N1 must NOT introduce a new storage truth layer.

## Hard anti-scope

- Do NOT expose raw local filesystem paths if the existing API does not already expose them safely.
- Do NOT fake versions when no `PresentationVersion` exists.
- Do NOT create presentations implicitly in retrieval routes.
- Do NOT silently return another user's presentation.
- Do NOT bypass owner/session checks.

## Acceptance criteria

- Generated or registered presentations can be listed for a session.
- One presentation can be fetched by id with safe metadata.
- Current file reference is visible in a stable schema.
- Missing/unauthorized presentations fail clearly.
- Existing slides generation and task execution tests still pass.

## Required tests

- List presentations by session.
- Get presentation metadata by id.
- Missing presentation returns expected error.
- Session/user isolation where current auth model supports it.
- Backward compatibility: existing slides generation still passes.

## Stop conditions

- If exposing presentations requires changing how artifacts are created, stop and report the smallest missing integration.
- If revision behavior becomes necessary, stop and leave it for N2.

---

# N2 — Deck revision API contract

## Goal

Expose M15 `DeckRevisionService` through a stable backend API contract.

## Current problem

M15 added a backend service-level deck revision flow, but clients cannot yet invoke it through a public API. The system needs a stable contract for slide and section revisions.

## Scope

Add API endpoints and schemas for deck revision operations.

Allowed changes:
- Revision request/response schemas.
- Route dependency wiring.
- Endpoint for regenerating one slide.
- Endpoint for regenerating one section/story stage.
- Endpoint for listing revision lineage.
- Tests using existing repositories and storage.
- Minimal plan-loading mechanism if a valid stored plan already exists.

## Minimum API shape

- `POST /presentations/{presentation_id}/revisions/slide`
- `POST /presentations/{presentation_id}/revisions/section`
- `GET /presentations/{presentation_id}/revisions`

Minimum request fields:
- instruction
- target slide id or target slide index for slide revision
- target story arc stage for section revision
- optional task id
- optional change summary
- optional template id if already known

Minimum response fields:
- presentation id
- version id
- version number
- parent version id
- stored file id
- revised slide ids
- scope
- change summary
- created timestamp

## Critical plan-source decision

N2 must not invent a plan if no plan is available. It must use one of these honest approaches:
1. load a previously persisted plan if already available;
2. require the client/test to provide a plan payload;
3. return a clear error saying revision cannot proceed because no editable plan representation is stored yet.

Any selected approach must be explicit in tests.

## Likely files

- `backend/app/api/routes/`
- `backend/app/api/schemas/`
- `backend/app/api/dependencies.py`
- `backend/app/composition.py`
- `backend/app/services/slides_service/revision.py` only if a small compatibility extension is required
- `backend/tests/api/`

## Adjacent issue firewall

- N2 must NOT implement provider-backed semantic rewriting. That belongs to N4.
- N2 must NOT build frontend editor UI.
- N2 must NOT redesign deck planning or rendering.
- N2 must NOT add visual smoke validation. That belongs to N5.
- N2 must NOT stabilize all slides API metadata. That belongs to N6.

## Hard anti-scope

- Do NOT rebuild the full deck blindly while claiming partial revision.
- Do NOT invent missing plan state.
- Do NOT lose template id where the request or stored metadata provides it.
- Do NOT expose unsafe storage keys if not part of the API contract.
- Do NOT weaken existing auth/session checks.

## Acceptance criteria

- Slide revision can be requested through API.
- Section revision can be requested through API.
- Revision lineage can be listed through API.
- Revision creates a new `PresentationVersion` and `StoredFile`.
- Current presentation file advances to the new revision.
- Failure modes are explicit for missing presentation, missing plan, invalid target, or unauthorized access.

## Required tests

- API slide revision success.
- API section revision success.
- API revision lineage listing.
- Missing presentation failure.
- Missing/invalid plan failure if relevant.
- Invalid target failure.
- Existing generation API remains compatible.

## Stop conditions

- If no honest plan-loading/provision mechanism exists, stop after adding schemas/service wiring and report the blocker.
- If frontend changes become necessary, stop.

---

# N3 — Revision persistence integration tests

## Goal

Prove revision flow works with real repository implementations, not only in-memory fakes.

## Current problem

M15 focused tests use memory fakes. That proves service semantics but not persistence integration with SQLite/Postgres-style repositories and local file storage.

## Scope

Add integration tests for revision persistence using accepted repository/storage abstractions.

Allowed changes:
- Tests for SQLite repositories if SQLite test profile exists.
- Tests for Postgres repositories only if the existing test infrastructure supports them.
- Small repository protocol/export fixes if a current implementation is missing but required by accepted models.
- No production truth-layer change.

## Minimum covered flow

- Create or register initial presentation.
- Create initial presentation version.
- Store initial/current file reference.
- Regenerate one slide.
- Assert new `StoredFile` exists.
- Assert new `PresentationVersion` exists.
- Assert parent version id is correct.
- Assert `Presentation.current_file_id` points to revised file.
- Assert lineage order is inspectable.

## Likely files

- `backend/tests/integrations/`
- `backend/tests/services/`
- `backend/app/repositories/sqlite.py` only if minimal missing repository support is discovered
- `backend/app/repositories/postgres.py` only if existing accepted mapping requires parity and tests can run honestly
- `backend/app/repositories/__init__.py`

## Adjacent issue firewall

- N3 must NOT expose revision API. That belongs to N2.
- N3 must NOT add semantic provider revision. That belongs to N4.
- N3 must NOT redesign metadata models.
- N3 must NOT make SQLite production truth.

## Hard anti-scope

- Do NOT skip persistence checks by falling back to in-memory fakes.
- Do NOT mark tests passed if storage bytes are not actually written.
- Do NOT add fake repository methods that do not persist.
- Do NOT require external services unless the existing integration profile already does.

## Acceptance criteria

- Revision persistence works with accepted repository implementation(s).
- Version lineage persists across service instances where applicable.
- Stored revision PPTX bytes are retrievable from storage.
- Existing test suite passes.

## Required tests

- SQLite revision persistence test.
- Stored bytes retrieval test.
- Version lineage order test.
- Presentation current file update test.

## Stop conditions

- If repository support is missing, implement the smallest honest repository method and test it.
- If Postgres cannot be run in current environment, do not fake Postgres success; document coverage gap.

---

# N4 — Provider-backed semantic revision strategy

## Goal

Replace deterministic placeholder revision text with a strategy interface and optional provider-backed semantic revision.

## Current problem

M15 has deterministic revision behavior that is useful for foundation tests but weak for product-quality editing. A real revision workflow needs a strategy boundary so LLM-backed rewriting can be added without breaking deterministic/offline tests.

## Scope

Add a revision strategy abstraction.

Allowed changes:
- `SlideRevisionStrategy` protocol or equivalent.
- `DeterministicRevisionStrategy` as default/test strategy.
- `LLMRevisionStrategy` using accepted provider/text-service layer.
- Configuration/wiring through accepted composition root if needed.
- No silent fallback in production mode.
- Focused tests for deterministic and provider-backed paths using fakes/mocks.

## Minimum behavior

- Strategy receives old slide, instruction, and optional source/context.
- Strategy returns revised slide content or a typed revision payload.
- DeckRevisionService delegates slide/section rewriting to the strategy.
- Deterministic behavior remains available for tests/offline mode.
- Provider failures fail honestly.

## Likely files

- `backend/app/services/slides_service/revision.py`
- new `backend/app/services/slides_service/revision_strategy.py` if separation is cleaner
- `backend/app/composition.py`
- LLM/text service integration files only if necessary
- `backend/tests/services/`

## Adjacent issue firewall

- N4 must NOT add new public API endpoints. That belongs to N2.
- N4 must NOT add non-GigaChat production provider activation.
- N4 must NOT add frontend editor UI.
- N4 must NOT redesign M9-M15 planning/rendering.
- N4 must NOT introduce public internet requirements.

## Hard anti-scope

- Do NOT silently fallback from configured LLM strategy to deterministic output in production mode.
- Do NOT fake LLM success.
- Do NOT log secrets, prompts containing secrets, or provider tokens.
- Do NOT replace accepted provider architecture.
- Do NOT make provider-backed revision mandatory for tests that should remain offline.

## Acceptance criteria

- Revision service can use a strategy object.
- Deterministic strategy preserves current test behavior.
- Provider-backed strategy can be tested with a fake provider/text service.
- Provider failure produces clear failure, not fake revision.
- Existing M15 revision tests pass.

## Required tests

- Deterministic strategy compatibility.
- Strategy delegation for one-slide revision.
- Strategy delegation for section revision.
- Fake provider-backed revision success.
- Provider failure fails honestly.

## Stop conditions

- If provider integration requires redesigning LLM services, stop and report the boundary gap.
- If production fallback semantics are unclear, stop before adding hidden fallback.

---

# N5 — Sample deck export and visual smoke validation

## Goal

Create stable sample decks and machine-check that generated PPTX files are structurally and visually smoke-testable.

## Current problem

M9-M15 tests validate PPTX zip structure and XML markers, but there is no explicit sample deck export pack and no optional smoke check that Office/LibreOffice can open/convert generated decks.

## Scope

Add sample generation and optional visual smoke validation.

Allowed changes:
- Sample deck generation fixtures/scripts under test or tools directory.
- Golden metadata for sample decks.
- Optional LibreOffice headless conversion smoke test if binary is available.
- Clear skip reason when external office tooling is absent.
- No public internet dependency.

## Minimum sample set

- text-only deck
- template/layout deck
- media/image deck
- structured table/chart deck
- source-grounded deck
- revised deck

## Likely files

- `backend/tests/services/`
- `backend/tests/smoke/`
- optional `tools/` or `scripts/` sample generator if repo conventions allow
- existing slides service files only if tiny testability hooks are required

## Adjacent issue firewall

- N5 must NOT add revision API.
- N5 must NOT add semantic provider revision.
- N5 must NOT add frontend preview.
- N5 must NOT require public internet.
- N5 must NOT fail environments solely because LibreOffice is absent.

## Hard anti-scope

- Do NOT commit large binary sample PPTX files unless explicitly approved.
- Do NOT make visual validation depend on network resources.
- Do NOT mark visual smoke success if conversion failed.
- Do NOT silently skip without an explicit reason.

## Acceptance criteria

- Sample decks can be generated deterministically.
- Each major M9-M15 feature path has a sample or smoke coverage.
- Optional conversion smoke is honest: pass if tool succeeds, skip with reason if unavailable, fail if available but conversion fails.
- Existing tests pass.

## Required tests

- Sample generation smoke.
- PPTX open/zip structure smoke for each sample.
- Optional LibreOffice conversion smoke with explicit skip.

## Stop conditions

- If sample export would require committing large binaries, stop and ask for artifact policy.
- If office tooling is absent, skip honestly rather than faking conversion.

---

# N6 — Slides API schema stabilization

## Goal

Stabilize public API contracts around slides generation, media metadata, source grounding, presentation retrieval, and revisions.

## Current problem

M12-M15 introduced useful metadata fields, but public response shapes can drift if internal dicts/dataclasses leak into API responses.

## Scope

Add or tighten Pydantic schemas for slides-related API responses.

Allowed changes:
- Explicit schemas for generated media refs.
- Explicit schemas for source grounding metadata.
- Explicit schemas for presentation metadata.
- Explicit schemas for revision metadata.
- Backward compatibility tests.
- Deprecation-safe aliases only if needed.

## Likely files

- `backend/app/api/schemas/`
- `backend/app/api/routes/`
- `backend/tests/api/`

## Adjacent issue firewall

- N6 must NOT add new revision capabilities. That belongs to N2/N4.
- N6 must NOT redesign storage/repository models.
- N6 must NOT expose unsafe internal storage keys by accident.
- N6 must NOT add frontend.

## Hard anti-scope

- Do NOT expose raw dataclass `__dict__` as API contract.
- Do NOT leak local filesystem paths or internal storage keys unless explicitly part of safe contract.
- Do NOT remove existing response fields without compatibility strategy.
- Do NOT silently coerce invalid metadata into success.

## Acceptance criteria

- Slides-related API responses use explicit schemas.
- Existing clients/tests keep working or have documented backward-compatible aliases.
- Metadata fields are stable and typed.
- Unsafe internal implementation details are not exposed.

## Required tests

- Slides generation response schema test.
- Presentation retrieval response schema test if N1 exists.
- Revision response schema test if N2 exists.
- Backward compatibility test for existing task result fields.

## Stop conditions

- If N1/N2 are not yet implemented, scope N6 to existing routes only and report deferred schema areas.
- If a field's public safety is unclear, do not expose it.

---

# N7 — Operational hardening and regression pack

## Goal

Lock down the full M9-N6 slides path with regression tests, review tactics, and phase completion documentation.

## Current problem

The slides subsystem now spans planning, rendering, media, image generation, structured blocks, source grounding, revision, and APIs. It needs a final regression suite and review checklist so later phases do not break it accidentally.

## Scope

Add a regression pack and review tactics for the slides product workflow.

Allowed changes:
- End-to-end backend regression tests.
- Sync and queued execution coverage.
- Regression matrix documentation.
- Review tactics document for future slides changes.
- Minimal test helpers.

## Required regression paths

- prompt-only text deck
- stored-source deck
- source-grounded deck
- deck with generated media/image pipeline
- deck with structured table/chart blocks
- revised deck
- queued execution path
- synchronous execution path
- presentation retrieval path if N1 exists
- revision API path if N2 exists

## Likely files

- `backend/tests/api/`
- `backend/tests/services/`
- `backend/tests/orchestrator/`
- `N_REVIEW_TACTICS.md`
- optional test helper modules

## Adjacent issue firewall

- N7 must NOT add new product capabilities.
- N7 must NOT add frontend.
- N7 must NOT redesign APIs.
- N7 must NOT introduce public internet dependencies.

## Hard anti-scope

- Do NOT weaken existing tests to reduce runtime.
- Do NOT replace focused tests with one broad brittle test.
- Do NOT skip core regression paths without explicit reason.
- Do NOT add flaky time/network dependencies.

## Acceptance criteria

- Regression suite covers accepted M9-N6 slides paths.
- Review tactics document exists and is specific to slides product workflow.
- Full backend test suite passes.
- Future phase risks are documented.

## Required tests

- End-to-end sync generation regression.
- End-to-end queued generation regression.
- Source-grounded regression.
- Revision regression.
- Structured blocks regression.

## Stop conditions

- If runtime becomes too high, split slow optional smoke tests from required regression tests without removing coverage.
- If a required path is blocked by earlier missing API work, document it and cover what exists honestly.
