# PROMPTS_1_5.md

## Prompt 1

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- docs/issue-pack.md
- README.start-here.md

Implement Issue 001 and Issue 002 only.

Goals:
- preserve the current bootstrap files and keep them working
- keep backend/app/main.py as the main backend entrypoint
- keep GET /health returning 200
- safely extend the repository skeleton for the planned architecture

Constraints:
- keep the project as a modular monolith
- do not introduce microservices
- do not delete existing bootstrap files
- keep FastAPI endpoints thin
- prefer explicit structure over placeholder comments
- add tests for any non-trivial new backend behavior

Acceptance criteria:
- repository structure is extended in a clean way
- backend still starts
- GET /health returns 200
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- changed files
- commands run
- test results
- any remaining TODOs
```

## Prompt 2

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/issue-pack.md

Implement Issue 003 only.

Goals:
- scaffold the frontend workspace shell in frontend/
- create a root page
- add placeholder panels for:
  - chat
  - file upload
  - task status
  - artifacts

Constraints:
- keep backend untouched unless absolutely necessary
- keep the UI simple and modular
- do not implement product logic yet
- do not add unnecessary styling complexity
- prefer a clean Next.js structure with small components

Acceptance criteria:
- frontend starts locally
- root page renders
- workspace shell is visible
- placeholder panels are clearly separated
- npm run lint passes
- npm run build passes

Run these checks:
- cd frontend && npm run lint
- cd frontend && npm run build

At the end, summarize:
- changed files
- commands run
- build/lint results
- any remaining TODOs
```

## Prompt 3

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/issue-pack.md

Implement Issue 004 and Issue 005 only.

Focus:
- core backend domain models
- schemas for sessions, tasks, artifacts, and uploaded files
- storage abstraction
- local file storage implementation
- deterministic artifact/file naming
- directory layout for uploads, artifacts, and temp files

Constraints:
- keep the project as a modular monolith
- do not add a real database ORM yet unless absolutely necessary
- prefer repository interfaces and clean dataclasses / pydantic schemas
- do not touch frontend in this task
- keep storage testable and local-first

Acceptance criteria:
- core domain model structure exists
- schemas are cleanly separated
- local file storage works
- storage path logic is deterministic and testable
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- changed files
- commands run
- test results
- any TODOs or follow-up recommendations
```

## Prompt 4

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/issue-pack.md

Implement Issue 006 only.

Focus:
- POST /sessions
- POST /uploads
- POST /tasks
- GET /tasks/{task_id}
- GET /sessions/{session_id}
- wire these routes through the current backend structure
- use the existing model/schema/storage abstractions

Constraints:
- keep endpoints thin
- do not implement real business workflows yet
- do not introduce background workers in this task
- uploaded files should be saved through the storage abstraction
- task persistence can be in-memory or simple repository-backed if clearly structured for future replacement

Acceptance criteria:
- session can be created
- file can be uploaded
- task can be created
- task can be queried
- session details can be fetched
- API tests are added
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- changed files
- commands run
- test results
- remaining TODOs
```

## Prompt 5

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/issue-pack.md

Implement Issue 007 and Issue 008 only.

Focus:
- artifact repository and artifact schemas
- GET /artifacts/{artifact_id}
- GET /sessions/{session_id}/artifacts
- orchestrator skeleton:
  - classifier.py
  - planner.py
  - tool_router.py
  - coordinator.py
  - result_composer.py
- initial task type enum:
  - docx_edit
  - pdf_summary
  - slides_generate
  - data_analysis

Constraints:
- do not implement full business workflows yet
- create clean service boundaries for later integration
- keep the orchestrator testable
- keep artifact API stable and simple
- keep backend modular-monolith style

Acceptance criteria:
- artifact metadata can be fetched
- session artifacts can be listed
- orchestrator can classify supported task types
- routing skeleton is testable
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- changed files
- commands run
- test results
- remaining TODOs
```
