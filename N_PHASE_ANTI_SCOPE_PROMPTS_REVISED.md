# N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md

This file contains self-contained Codex prompts for N1-N7.
Each prompt is copy-paste ready and explicitly reads `N_PHASE_ISSUE_PACK.md`.

---

# Prompt N1 — Presentation artifact registry and retrieval API

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F-M8 and M9-M15 phases are accepted.
Do not re-litigate accepted F-M15 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, source extraction model, slides planning model, layout/template engine, media foundation, image pipeline, structured slide blocks, source-aware grounding model, or deck revision service unless this issue explicitly says so.

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
4. Explicitly confirm accepted F-M15 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F-M15 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple N issues in one run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene
7. Backward compatibility
8. Product contract clarity

Reject if:
- adjacent issue work was implemented
- accepted architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into the offline intranet profile
- unsafe storage details are exposed accidentally
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/routes/
- backend/app/api/schemas/
- backend/app/api/dependencies.py
- backend/app/composition.py
- backend/app/domain/metadata/models.py
- backend/app/repositories/
- backend/app/services/slides_service/
- backend/tests/api/

Implement N1 only.

Issue scope:
Expose generated presentations as first-class retrievable backend entities.

Allowed changes:
- presentation response schemas
- list presentations by session route
- get one presentation metadata route
- safe current file reference exposure
- optional version summary if already backed by existing repositories
- composition-root dependency wiring
- focused API tests

Minimum API shape:
- GET /sessions/{session_id}/presentations
- GET /presentations/{presentation_id}

Adjacent issue firewall:
- N1 must NOT add deck revision endpoints. That belongs to N2.
- N1 must NOT add provider-backed semantic revision. That belongs to N4.
- N1 must NOT add frontend editor UI.
- N1 must NOT redesign M15 revision service.
- N1 must NOT introduce a new storage truth layer.

Hard anti-scope:
- Do NOT expose raw local filesystem paths if the existing API does not already expose them safely.
- Do NOT fake versions when no PresentationVersion exists.
- Do NOT create presentations implicitly in retrieval routes.
- Do NOT silently return another user's presentation.
- Do NOT bypass owner/session checks.

Acceptance criteria:
- Presentations can be listed for a session.
- One presentation can be fetched by id.
- Current file reference is visible in a safe stable schema.
- Missing/unauthorized presentations fail clearly.
- Existing slides generation and task execution tests still pass.

Required tests:
- list presentations by session
- get presentation metadata by id
- missing presentation failure
- session/user isolation where current auth model supports it
- backward compatibility for existing slides generation
```

---

# Prompt N2 — Deck revision API contract

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F-M8, M9-M15, and N1 are accepted.
Do not re-litigate accepted architecture.
Do not replace composition root, execution coordinator, storage model, provider model, source extraction model, slides planning/layout/media/image/blocks/source-grounding/revision services, or N1 presentation retrieval unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against live file instead of forcing earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Confirm adjacent issues were not implemented.
4. Confirm accepted F-M15/N1 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend

Stop conditions:
- If no honest plan-loading/provision mechanism exists, stop after smallest safe subset and report blocker.
- If frontend changes become necessary, stop.
- If a change would create fake success behavior, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F-M15/N1 architecture.
- Replace composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite production truth.
- Store binary files primarily in Postgres.
- Activate non-GigaChat provider in deployment.
- Add public-internet assumptions.
- Add fake success paths.
- Hide missing infrastructure behind fallback.
- Remove tests to pass.
- Touch frontend.
- Implement N3/N4/N5/N6/N7.
```

## Review gate for this issue

```text
Reject if:
- endpoint invents missing editable plan state
- revision claims partial update while blindly regenerating all slide models
- template/theme is lost despite being available
- unsafe storage details leak
- auth/session checks are weakened
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/revision.py
- backend/app/api/routes/
- backend/app/api/schemas/
- backend/app/api/dependencies.py
- backend/app/composition.py
- backend/app/repositories/
- backend/tests/api/

Implement N2 only.

Issue scope:
Expose M15 DeckRevisionService through backend API.

Allowed changes:
- revision request/response schemas
- route dependency wiring
- endpoint for one-slide revision
- endpoint for one-section revision
- endpoint for revision lineage listing
- focused API tests
- minimal honest plan provision/loading if already available

Minimum API shape:
- POST /presentations/{presentation_id}/revisions/slide
- POST /presentations/{presentation_id}/revisions/section
- GET /presentations/{presentation_id}/revisions

Critical rule:
Do not invent a plan if no editable plan representation exists. Either load an existing stored plan, require explicit plan payload, or fail clearly.

Adjacent issue firewall:
- N2 must NOT add provider-backed semantic rewriting. That belongs to N4.
- N2 must NOT build frontend editor UI.
- N2 must NOT add visual smoke validation. That belongs to N5.
- N2 must NOT stabilize all slides API metadata. That belongs to N6.

Acceptance criteria:
- API slide revision creates PresentationVersion + StoredFile.
- API section revision creates PresentationVersion + StoredFile.
- Revision lineage can be listed.
- Current presentation file advances to revised file.
- Missing presentation, missing plan, invalid target, unauthorized access fail clearly.
```

---

# Prompt N3 — Revision persistence integration tests

## Global Codex contract for this issue

```text
Work from repository root.

F-M8, M9-M15, N1, and N2 are accepted.
Do not redesign accepted architecture. This is a persistence verification issue, not a product capability issue.

Current-branch-state rules:
- Work against CURRENT checked-out branch state.
- Inspect live files before planning.
- Do not patch stale contents.
- Prefer additive tests and minimal repository fixes.
- If patch compatibility is uncertain, stop and report exact files.

Mandatory before coding:
1. List files inspected.
2. Describe current persistence behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary.
5. State adjacent issues intentionally NOT implemented.
6. State tests to add/update.

Mandatory after coding:
1. Summarize only N3 changes.
2. List files changed.
3. Confirm no new capabilities outside persistence tests.
4. Confirm accepted architecture preserved.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend
```

## Anti-scope

```text
Do NOT:
- Expose new API capabilities.
- Add semantic revision strategy.
- Redesign metadata models.
- Make SQLite production truth.
- Fake repository persistence.
- Skip storage-byte checks.
- Add public-internet dependencies.
- Remove or weaken existing tests.
```

## Review gate

```text
Reject if:
- tests use only in-memory fakes for N3 acceptance
- storage bytes are not actually written/read
- version lineage is not verified
- repository implementation is fake/no-op
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/revision.py
- backend/app/repositories/sqlite.py
- backend/app/repositories/postgres.py
- backend/app/repositories/interfaces.py
- backend/app/repositories/storage.py
- backend/tests/integrations/
- backend/tests/services/test_m15_deck_revision.py

Implement N3 only.

Issue scope:
Prove revision persistence works with accepted repository/storage implementations.

Allowed changes:
- SQLite revision persistence integration tests
- Postgres coverage only if existing infrastructure supports it honestly
- tiny repository protocol/export fixes if missing and directly required
- local storage test fixtures

Required assertions:
- StoredFile is persisted.
- PresentationVersion is persisted.
- parent_version_id is correct.
- Presentation.current_file_id advances.
- revision PPTX bytes are retrievable.
- lineage is ordered and durable.

Stop conditions:
- If Postgres cannot run in current environment, do not fake it; document coverage gap.
- If repository support is missing, implement smallest honest method and test it.
```

---

# Prompt N4 — Provider-backed semantic revision strategy

## Global Codex contract for this issue

```text
Work from repository root.

F-M8, M9-M15, and N1-N3 are accepted.
Do not redesign accepted architecture. Add a strategy boundary for revision semantics only.

Current-branch-state rules:
- Work against CURRENT checked-out branch state.
- Inspect live files before planning.
- Prefer additive strategy files over broad rewrites.
- Stop if provider wiring would require architecture redesign.

Mandatory before coding:
1. List files inspected.
2. Describe current deterministic revision behavior.
3. List files planned for change.
4. Explain why each file is necessary.
5. State adjacent issues NOT implemented.
6. State tests to add/update.

Mandatory after coding:
1. Summarize only N4 changes.
2. List files changed.
3. Confirm no API/frontend expansion unless already accepted contract needs wiring.
4. Confirm no provider fallback fakery.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend
```

## Anti-scope

```text
Do NOT:
- Add new public API endpoints.
- Activate non-GigaChat production provider.
- Replace accepted provider architecture.
- Add public internet requirement.
- Silently fallback from provider strategy to deterministic strategy in production.
- Fake LLM success.
- Log secrets or provider tokens.
- Build frontend editor UI.
```

## Review gate

```text
Reject if:
- configured provider failure becomes fake deterministic success
- strategy is hardcoded into routes instead of injected/composed cleanly
- deterministic tests become network-dependent
- provider secrets are logged
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/revision.py
- backend/app/services/llm_text_service.py or current text provider service files
- backend/app/composition.py
- backend/tests/services/test_m15_deck_revision.py

Implement N4 only.

Issue scope:
Add provider-backed semantic revision strategy while preserving deterministic offline behavior.

Allowed changes:
- SlideRevisionStrategy protocol
- DeterministicRevisionStrategy
- LLMRevisionStrategy using accepted provider/text-service layer
- DeckRevisionService delegation to strategy
- composition-root wiring if needed
- focused tests with fakes/mocks

Acceptance criteria:
- Revision service accepts/uses a strategy.
- Deterministic strategy preserves current tests.
- Fake provider-backed strategy test proves semantic delegation.
- Provider failure fails honestly.
- No silent production fallback.
```

---

# Prompt N5 — Sample deck export and visual smoke validation

## Global Codex contract for this issue

```text
Work from repository root.

F-M8, M9-M15, and N1-N4 are accepted.
This is a smoke/hardening issue, not a new product capability issue.

Current-branch-state rules:
- Work against CURRENT checked-out branch state.
- Inspect live files before planning.
- Prefer additive tests/scripts.
- Stop before committing large binary artifacts unless explicitly approved.

Mandatory before coding:
1. List files inspected.
2. Describe current sample/smoke coverage.
3. List files planned for change.
4. Explain why each file is necessary.
5. State adjacent issues NOT implemented.
6. State tests to add/update.

Mandatory after coding:
1. Summarize only N5 changes.
2. List files changed.
3. Confirm no new product/API capability was added.
4. Confirm no public internet dependency.
5. List commands run.
6. Report test results and any explicit skips.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend
```

## Anti-scope

```text
Do NOT:
- Commit large binary PPTX files without explicit approval.
- Require public internet.
- Make LibreOffice mandatory in environments where it is unavailable.
- Silently skip visual smoke without explicit reason.
- Add frontend preview.
- Add new revision/API capability.
```

## Review gate

```text
Reject if:
- smoke success is claimed when conversion failed
- skip lacks explicit reason
- generated samples are nondeterministic without reason
- large binaries are committed accidentally
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/
- backend/tests/services/
- backend/tests/smoke/

Implement N5 only.

Issue scope:
Add deterministic sample deck generation and optional visual smoke validation.

Minimum sample set:
- text-only deck
- layout/template deck
- media/image deck
- structured table/chart deck
- source-grounded deck
- revised deck

Allowed changes:
- sample generation test helpers
- smoke tests
- optional LibreOffice headless conversion check with explicit skip
- no large binary commits unless explicitly approved

Acceptance criteria:
- samples generate deterministically
- PPTX zip structure validates for each sample
- optional office conversion passes or skips honestly
- existing tests pass
```

---

# Prompt N6 — Slides API schema stabilization

## Global Codex contract for this issue

```text
Work from repository root.

F-M8, M9-M15, and N1-N5 are accepted.
Do not redesign accepted services. Stabilize public schemas only.

Current-branch-state rules:
- Work against CURRENT checked-out branch state.
- Inspect live API routes/schemas before planning.
- Prefer additive schemas and backward-compatible aliases.
- Stop if public safety of a field is unclear.

Mandatory before coding:
1. List files inspected.
2. Describe current API schema behavior.
3. List files planned for change.
4. Explain why each file is necessary.
5. State adjacent issues NOT implemented.
6. State tests to add/update.

Mandatory after coding:
1. Summarize only N6 changes.
2. List files changed.
3. Confirm no new product capability was added.
4. Confirm unsafe internals are not exposed.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend
```

## Anti-scope

```text
Do NOT:
- Add new revision capabilities.
- Redesign storage/repositories.
- Expose raw dataclass __dict__ as API contract.
- Leak local filesystem paths or unsafe storage keys.
- Remove existing response fields without compatibility strategy.
- Silently coerce invalid metadata into success.
- Add frontend.
```

## Review gate

```text
Reject if:
- internal dataclasses leak as public API
- unsafe storage details are exposed accidentally
- existing clients/tests lose fields without migration
- schema tests are missing
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/schemas/
- backend/app/api/routes/
- backend/tests/api/

Implement N6 only.

Issue scope:
Stabilize public schemas for slides generation, presentation retrieval, media metadata, source grounding, and revisions.

Allowed changes:
- explicit response schemas
- generated media ref schema
- source grounding metadata schema
- presentation metadata schema
- revision metadata schema
- backward compatibility tests

Acceptance criteria:
- slides-related API responses use explicit schemas
- metadata fields are typed and stable
- unsafe internals are not exposed
- existing behavior remains backward-compatible
```

---

# Prompt N7 — Operational hardening and regression pack

## Global Codex contract for this issue

```text
Work from repository root.

F-M8, M9-M15, and N1-N6 are accepted.
This is the final N-phase regression/hardening issue. Do not add new product capabilities.

Current-branch-state rules:
- Work against CURRENT checked-out branch state.
- Inspect live tests and docs before planning.
- Prefer additive regression tests and review documentation.
- Do not weaken existing tests for runtime convenience.

Mandatory before coding:
1. List files inspected.
2. Describe current regression coverage.
3. List files planned for change.
4. Explain why each file is necessary.
5. State adjacent/future issues NOT implemented.
6. State tests/docs to add/update.

Mandatory after coding:
1. Summarize only N7 changes.
2. List files changed.
3. Confirm no new product capability was added.
4. Confirm accepted F-M15/N1-N6 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- python3 -m pytest -q
- python3 -m compileall backend
```

## Anti-scope

```text
Do NOT:
- Add new API/product capability.
- Add frontend.
- Redesign APIs/services.
- Introduce public internet dependency.
- Replace focused tests with one broad brittle test.
- Skip core regression paths without explicit reason.
- Add flaky time/network dependencies.
- Remove or weaken existing tests.
```

## Review gate

```text
Reject if:
- regression pack misses accepted major slides paths without explanation
- tests are flaky or network-dependent
- frontend/product capability is added
- review tactics are generic rather than slides-specific
- python3 pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- N_PHASE_ISSUE_PACK.md
- N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/tests/api/
- backend/tests/services/
- backend/tests/orchestrator/
- backend/app/services/slides_service/

Implement N7 only.

Issue scope:
Lock down the full accepted slides product workflow with regression tests and review tactics.

Required regression paths:
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

Allowed changes:
- additive backend regression tests
- `N_REVIEW_TACTICS.md`
- small test helpers

Acceptance criteria:
- regression pack covers accepted M9-N6 slides paths
- review tactics document exists and is slides-product specific
- full backend test suite passes
- future phase risks are documented
```
