# NEXT_PHASE_ISSUE_PACK.md

## Next Phase Issue Pack — KW Studio

This issue pack defines the next implementation phase after the initial bootstrap, orchestrator skeleton, and legacy migration foundation.

The goal of this phase is to move KW Studio from a clean architectural skeleton toward a real artifact-producing MVP.

Priority order:
1. persistence
2. artifacts
3. orchestrator execution
4. DOCX/PDF deep integration
5. PPTX MVP

---

## Phase A — Persistence Phase

### Issue A1 — Introduce persistent repositories

#### Goal
Replace in-memory repositories with persistent implementations.

#### Scope
- add persistent repository implementations for:
  - sessions
  - tasks
  - artifacts
  - uploaded files
- keep repository interfaces stable where possible
- wire persistent repositories into app bootstrap/container
- preserve current API behavior

#### Suggested target files
- `backend/app/repositories/`
- `backend/app/integrations/database/`
- `backend/app/api/dependencies.py` or new container/bootstrap module
- new DB models/mapping modules if needed

#### Constraints
- keep modular monolith architecture
- do not rewrite unrelated service logic
- do not break current tests without replacing them with persistent equivalents
- keep in-memory implementations only if needed for tests/dev, but make persistent repos the default app path

#### Acceptance criteria
- sessions persist across process restart
- tasks persist across process restart
- artifacts persist across process restart
- uploaded file metadata persists across process restart
- repository tests cover CRUD basics
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue A2 — Add DB bootstrap and migration baseline

#### Goal
Create a minimal, maintainable persistence bootstrap.

#### Scope
- add database settings wiring
- add database initialization path
- add migration baseline structure
- document local DB startup and migration flow

#### Suggested target files
- `backend/app/core/config.py`
- `backend/app/integrations/database/`
- `scripts/migrations/`
- `README.md` or `README.start-here.md`

#### Constraints
- keep it simple
- no unnecessary infrastructure complexity
- prefer a clear migration path over premature abstraction

#### Acceptance criteria
- local DB setup is documented
- migrations/baseline init path exists
- app can start with persistence enabled
- tests still pass

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

## Phase B — Artifact Phase

### Issue B1 — Make artifacts real storage-backed outputs

#### Goal
Turn artifacts into real downloadable files, not only metadata objects.

#### Scope
- extend artifact model with:
  - storage path or storage key
  - mime type
  - filename
  - size if available
- update artifact service to save files through storage abstraction
- ensure artifact metadata and file location stay linked

#### Suggested target files
- `backend/app/services/artifact_service/`
- `backend/app/domain/artifacts/`
- `backend/app/repositories/`
- `backend/app/integrations/file_storage/`

#### Constraints
- do not bypass storage abstraction
- preserve backward compatibility where reasonable
- keep artifact service focused on artifact lifecycle

#### Acceptance criteria
- artifact creation writes a real file or managed placeholder file
- artifact metadata references actual stored content
- artifact retrieval path is deterministic
- tests cover artifact creation and lookup
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue B2 — Add artifact download API

#### Goal
Allow the UI and clients to download generated artifacts.

#### Scope
- add file download endpoint
- support artifact metadata fetch + actual file response
- return appropriate content type and filename
- add tests for missing artifact and successful download

#### Suggested target files
- `backend/app/api/routes/artifacts.py`
- `backend/app/services/artifact_service/`
- `backend/tests/api/`

#### Constraints
- keep routes thin
- do not embed storage logic directly in route handlers
- preserve clean service boundaries

#### Acceptance criteria
- artifact metadata endpoint works
- artifact download endpoint returns actual file content
- invalid artifact IDs return proper errors
- tests cover both metadata and download flow
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

## Phase C — Orchestrator Execution Phase

### Issue C1 — Implement task execution lifecycle

#### Goal
Turn tasks from static records into executable units.

#### Scope
- add task lifecycle transitions:
  - pending
  - running
  - succeeded
  - failed
- implement application service or coordinator path that executes a task
- capture structured task result data
- persist task state changes

#### Suggested target files
- `backend/app/orchestrator/`
- `backend/app/services/session_task_service.py`
- `backend/app/domain/tasks/`
- `backend/app/repositories/`

#### Constraints
- keep transport concerns out of the core execution logic
- no browser-heavy features in this phase
- keep execution path understandable and testable

#### Acceptance criteria
- task can move through a real lifecycle
- success and failure states are persisted
- execution result is captured in a structured way
- tests cover lifecycle transitions
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue C2 — Wire orchestrator to service execution

#### Goal
Make the orchestrator actually call service entrypoints based on task type.

#### Scope
- route supported task types to service handlers:
  - docx_edit
  - pdf_summary
  - data_analysis
  - slides_generate (stub execution path allowed initially)
- create a stable execution contract between orchestrator and services
- persist task outputs and artifact references

#### Suggested target files
- `backend/app/orchestrator/coordinator.py`
- `backend/app/orchestrator/router.py`
- `backend/app/orchestrator/tool_router.py`
- `backend/app/orchestrator/result_composer.py`
- `backend/app/services/*`

#### Constraints
- keep orchestrator focused on orchestration, not domain logic
- do not overbuild a workflow engine
- preserve testability

#### Acceptance criteria
- orchestrator selects the right service path
- service results can produce task result + artifact reference
- basic integration tests exist
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

## Phase D — DOCX/PDF Deep Integration Phase

### Issue D1 — Deepen DOCX workflow using migrated skill assets

#### Goal
Replace placeholder DOCX editing with a more realistic DOCX transformation path.

#### Scope
- integrate migrated DOCX skill logic into `docx_service`
- support at least one meaningful editing workflow beyond plain text replace
- preserve document-oriented output behavior
- create artifact output using the real artifact pipeline

#### Suggested target files
- `skills/docx/`
- `backend/app/services/docx_service/`
- `backend/tests/services/`

#### Constraints
- do not expose low-level skill internals directly to API routes
- keep service wrapper explicit
- prefer one strong workflow over many weak ones

#### Acceptance criteria
- DOCX service uses migrated skill assets
- at least one real DOCX transformation workflow works end-to-end
- resulting artifact is downloadable
- tests cover service behavior
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue D2 — Deepen PDF workflow using migrated skill assets

#### Goal
Replace placeholder PDF summarization logic with a real extraction and summary pipeline.

#### Scope
- integrate migrated PDF skill logic into `pdf_service`
- extract text or structured content from PDF
- build summary output from extracted content
- produce downloadable artifact where appropriate

#### Suggested target files
- `skills/pdf/`
- `backend/app/services/pdf_service/`
- `backend/tests/services/`

#### Constraints
- keep service wrapper thin
- preserve clear boundary between low-level PDF logic and service orchestration
- do not introduce browser-heavy PDF flows yet unless necessary

#### Acceptance criteria
- PDF service uses migrated PDF skill assets
- extraction + summary path works end-to-end
- output is persisted through artifact pipeline if applicable
- tests cover extraction and summary behavior
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue D3 — Connect data analysis to a real kernel execution path

#### Goal
Move data analysis from skeleton status to real execution.

#### Scope
- implement a minimal real execution path through kernel runtime
- support at least one basic analysis flow for CSV/XLSX
- capture result text and optional chart/data artifacts
- keep runtime integration internal

#### Suggested target files
- `backend/app/runtime/kernel/`
- `backend/app/services/data_service/`
- `backend/app/orchestrator/`
- `backend/tests/runtime/`
- `backend/tests/services/`

#### Constraints
- no import-time side effects
- keep runtime lifecycle explicit
- keep the first implementation minimal and testable

#### Acceptance criteria
- data analysis invokes a real execution path
- result can be persisted as task output and/or artifact
- runtime smoke tests exist
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

## Phase E — PPTX MVP Phase

### Issue E1 — Add slides service MVP execution path

#### Goal
Create the first real slides generation path in the new architecture.

#### Scope
- implement `slides_service` execution entrypoint
- support input from:
  - plain notes
  - summary text
  - extracted source content from previous workflows
- generate a simple deck structure
- persist `.pptx` as an artifact

#### Suggested target files
- `backend/app/services/slides_service/`
- `backend/app/orchestrator/`
- `backend/app/services/artifact_service/`
- `backend/tests/services/`

#### Constraints
- keep PPTX MVP narrow
- fixed template or minimal template system is enough
- no complex visual editor
- no browser-heavy enhancement in this phase unless absolutely required
- focus on reliable artifact generation

#### Acceptance criteria
- slides task can run through orchestrator
- a `.pptx` artifact is created and stored
- artifact can be downloaded
- tests cover basic slides generation path
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

### Issue E2 — Add outline-first slides generation

#### Goal
Improve PPTX MVP by introducing an outline step before deck generation.

#### Scope
- add simple outline builder
- generate 5–10 slide deck from outline
- keep output deterministic enough for testing
- persist deck metadata and artifact

#### Suggested target files
- `backend/app/services/slides_service/outline.py`
- `backend/app/services/slides_service/generator.py`
- `backend/tests/services/`

#### Constraints
- no advanced design engine yet
- no template marketplace
- no browser-first layout engine
- keep first version testable and small

#### Acceptance criteria
- outline is generated before deck creation
- deck generation consumes outline cleanly
- resulting `.pptx` remains downloadable
- tests cover outline + generation flow
- pytest passes
- backend compiles

#### Required checks
- `pytest -q`
- `python -m compileall backend`

---

## Recommended implementation order

1. Issue A1
2. Issue A2
3. Issue B1
4. Issue B2
5. Issue C1
6. Issue C2
7. Issue D1
8. Issue D2
9. Issue D3
10. Issue E1
11. Issue E2
