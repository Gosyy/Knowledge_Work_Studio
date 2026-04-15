# M_PHASE_ISSUE_PACK.md

# KW Studio — M-phase Issue Pack

## Phase goal

M-phase moves KW Studio from the accepted F–L backend MVP foundation into productization and production scaffold.

F–L is accepted. Do not re-litigate F–L decisions.

Accepted baseline:
- Postgres is the metadata truth layer.
- Storage backend is the binary truth layer.
- GigaChat is the only active deployment provider.
- SQLite is allowed only for development/tests.
- Offline intranet deployment is the approved target.
- Official runtime flow is already real.
- Composition root is explicit.
- Transitional orchestration surfaces were removed.
- DOCX and PPTX outputs are real valid artifacts.
- PDF behavior must remain honest; no fake PDF success.
- Source lineage/provenance is part of the architecture.

## Global execution rules

Codex must:
- work from the current checked-out branch state
- inspect live file contents before planning
- avoid stale patches
- prefer additive/minimal changes
- preserve accepted F–L architecture
- run `pytest -q`
- run `python -m compileall backend`
- report exact files changed
- explicitly confirm adjacent issues were not implemented

Do not run multiple M issues in one Codex task.

## Global hard boundaries

Do NOT:
- redesign accepted F–L architecture
- replace composition root with route-local wiring
- reintroduce removed orchestration surfaces
- make SQLite production truth layer
- store binary files primarily in Postgres
- make non-GigaChat provider active in deployment
- add public-internet assumptions
- create fake success paths
- silently fallback from configured production services
- remove tests merely to pass the suite
- change frontend unless an issue explicitly allows it

---

# M0 — M-phase planning docs

## Goal
Create M-phase planning and review documents.

## Scope
Create or update:
- `M_PHASE_ISSUE_PACK.md`
- `M_REVIEW_TACTICS.md`
- `M_ANTI_SCOPE_PROMPTS_REVISED.md`

## Allowed changes
Documentation only.

## Anti-scope
Do NOT implement backend code, change runtime behavior, change frontend, add dependencies, or change F–L decisions.

## Acceptance criteria
- M issues M1–M8 are defined clearly.
- Each issue has scope, anti-scope, likely files, acceptance criteria, tests, and stop conditions.
- Review tactics include Scope, Architecture, Truth-layer, Reality, Tests, and Hygiene gates.

## Required checks
```bash
python -m compileall backend
```

---

# M1 — Auth/users domain foundation

## Goal
Add the backend foundation for real users and authentication primitives.

## Scope
Add:
- user domain model
- password hash abstraction or password service
- user repository protocol
- Postgres user repository
- SQLite user repository only for tests/dev consistency
- schema/bootstrap additions for users
- focused domain/repository tests

## Likely files
- `backend/app/domain/`
- `backend/app/domain/users/`
- `backend/app/repositories/interfaces.py`
- `backend/app/repositories/postgres.py`
- `backend/app/repositories/sqlite.py`
- `backend/app/repositories/__init__.py`
- `backend/app/integrations/database/bootstrap.py`
- `scripts/migrations/0001_repository_baseline.sql`
- `backend/tests/domain/`
- `backend/tests/integrations/`

## Anti-scope
Do NOT enforce ownership yet, add frontend login UI, implement OAuth, add broad RBAC, change task/session/artifact access behavior, or store plaintext passwords.

## Acceptance criteria
- User entity exists in domain code.
- User persistence exists for Postgres.
- SQLite support exists only for tests/dev if needed.
- Password handling is not plaintext.
- Existing tests pass.
- No ownership enforcement behavior changed.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M2 — Ownership enforcement

## Goal
Enforce explicit ownership over resources.

## Scope
Protect:
- sessions
- tasks
- uploaded files
- stored files
- artifacts

Add:
- current-user dependency
- test-safe identity mechanism
- owner-aware repository/service methods
- API tests proving cross-user access is denied

## Likely files
- `backend/app/api/dependencies.py`
- `backend/app/api/routes/sessions.py`
- `backend/app/api/routes/tasks.py`
- `backend/app/api/routes/uploads.py`
- `backend/app/api/routes/artifacts.py`
- `backend/app/services/session_task_service.py`
- `backend/app/services/artifact_service.py`
- `backend/app/services/task_source_service.py`
- `backend/app/domain/`
- `backend/app/repositories/`
- `backend/tests/api/`

## Anti-scope
Do NOT redesign M1 auth primitives, implement OAuth, build frontend auth screens, implement full RBAC, change artifact generation behavior except ownership enforcement, or rely on session IDs as implicit ownership.

## Acceptance criteria
- User A cannot access User B resources.
- Owner relation is explicit or reliably enforced.
- Artifact download is protected.
- Existing owner-valid flows still work.
- Cross-user tests pass with 403 or 404.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M3 — Alembic migration workflow

## Goal
Introduce production-grade schema migration workflow.

## Scope
Add:
- `alembic.ini`
- Alembic `migrations/env.py`
- first migration matching current approved schema
- migration docs
- smoke tests for migration configuration

## Likely files
- `alembic.ini`
- `migrations/`
- `scripts/migrations/`
- `backend/app/integrations/database/bootstrap.py`
- `backend/app/core/config.py`
- `requirements.txt`
- `backend/tests/integrations/`

## Anti-scope
Do NOT redesign schema, make SQLite production migration target, remove bootstrap unless safely replaced, invent new product entities, change API behavior, or implement auth if M1 is not accepted.

## Acceptance criteria
- Alembic is documented as production migration path.
- Current approved schema is represented in migration.
- Existing bootstrap compatibility is preserved or safely deprecated.
- Tests pass.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M4 — Background job queue foundation

## Goal
Add task execution queue foundation without breaking synchronous execution.

## Scope
Add:
- job domain model
- queue abstraction
- in-process test queue
- worker skeleton
- optional repository support
- enqueue/queued execution path
- tests proving queued task execution uses real execution path

## Likely files
- `backend/app/domain/tasks/models.py`
- `backend/app/services/task_execution_service.py`
- `backend/app/orchestrator/execution.py`
- `backend/app/api/routes/tasks.py`
- `backend/app/repositories/`
- `backend/app/runtime/workers/`
- `backend/tests/api/`
- `backend/tests/services/`
- `backend/tests/runtime/`

## Anti-scope
Do NOT add Celery/RQ/Redis unless explicitly allowed later, remove synchronous execution, fake job success, bypass provenance/source handling, change artifact semantics, or implement observability stack.

## Acceptance criteria
- Synchronous execution still works.
- Queued execution has honest lifecycle.
- Worker skeleton runs through official execution path.
- Failed jobs are represented honestly.
- Tests prove queued execution creates expected results/artifacts.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M5 — MinIO/S3-compatible storage adapter

## Goal
Implement real offline-intranet remote object storage support.

## Scope
Add:
- S3-compatible/MinIO storage adapter
- config wiring
- readiness validation
- tests using mocked/fake client
- docs update

## Likely files
- `backend/app/composition.py`
- `backend/app/deployment.py`
- `backend/app/core/config.py`
- `backend/app/integrations/file_storage/`
- `backend/app/repositories/storage.py`
- `docs/deployment/offline_intranet.md`
- `.env.example`
- `backend/tests/integrations/`
- `backend/tests/test_l3_deployment_hardening.py`

## Anti-scope
Do NOT require public internet, hardcode credentials, silently fallback to local storage, store binary payloads in Postgres, fake remote storage success, or implement binary extraction.

## Acceptance criteria
- `STORAGE_BACKEND=minio` or `s3` uses real adapter path.
- Missing remote config fails readiness.
- Adapter is testable without public internet.
- Local storage still works.
- Existing artifact behavior is preserved.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M6 — Frontend API integration contract

## Goal
Document and stabilize the frontend-facing API contract.

## Scope
Add:
- API contract docs
- request/response examples
- endpoint usage examples
- OpenAPI/schema cleanup only if non-breaking
- schema stability tests if practical

## Likely files
- `backend/app/api/routes/`
- `backend/app/api/schemas/`
- `backend/app/main.py`
- `.env.example`
- `docs/api/`
- `backend/tests/api/`

## Anti-scope
Do NOT build full frontend UI, redesign backend workflows, add auth UI, change task execution behavior, rename endpoints without compatibility, or add new product capabilities.

## Acceptance criteria
Frontend developers can understand how to call health/readiness, sessions, uploads, tasks, semantic tasks, and artifacts. Existing API tests pass.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M7 — Observability baseline

## Goal
Add dependency-light production observability baseline.

## Scope
Add:
- structured logging config
- request ID middleware
- request metadata logging
- task execution correlation logging
- readiness logging
- safe error logging
- optional dependency-free metrics skeleton

## Likely files
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/deployment.py`
- `backend/app/services/task_execution_service.py`
- `backend/app/orchestrator/execution.py`
- `backend/tests/`

## Anti-scope
Do NOT add full Prometheus/Grafana stack, add Sentry external calls, make external network calls, log secrets, log GigaChat tokens, log file contents, or change business behavior.

## Acceptance criteria
- Logs include request/task correlation where available.
- Sensitive values are not logged.
- Existing tests pass.
- New tests cover request ID/logging behavior where practical.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# M8 — Binary source extraction

## Goal
Allow selected binary source files to feed official execution honestly.

## Scope
Start with:
- DOCX text extraction
- PPTX outline/text extraction
- PDF text extraction only if safe and honest

Add:
- extractor interfaces
- format-specific extractors
- `TaskSourceService` integration
- derived content cache reuse
- tests with small generated binary samples

## Likely files
- `backend/app/services/task_source_service.py`
- `backend/app/services/docx_service/`
- `backend/app/services/pdf_service/`
- `backend/app/services/slides_service/`
- `backend/app/domain/metadata/models.py`
- `backend/app/repositories/`
- `backend/tests/api/`
- `backend/tests/services/`

## Anti-scope
Do NOT implement OCR, fake PDF extraction, claim unsupported formats work, silently decode binary garbage as text, bypass derived content cache, implement remote storage adapter, or add public-internet dependencies.

## Acceptance criteria
- Supported binary uploaded/stored sources can feed official execution.
- Unsupported formats fail with clear honest error.
- Extracted text is cached in `derived_contents`.
- Existing text-source flows still pass.

## Required checks
```bash
pytest -q
python -m compileall backend
```

---

# Recommended M-phase order

```text
M0 -> ACCEPT
M1 -> ACCEPT
M2 -> ACCEPT
M3 -> ACCEPT
M4 -> ACCEPT
M5 -> ACCEPT
M6 -> ACCEPT
M7 -> ACCEPT
M8 -> ACCEPT
```

Do not run adjacent issues together.
