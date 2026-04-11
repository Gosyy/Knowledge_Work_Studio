# CODEX_RUNBOOK.md

## Purpose

This runbook gives a complete, practical workflow for starting **KW Studio** from the prepared bootstrap package and then developing it in **Codex** through the first five implementation runs.

It covers:

- unpacking the repository bootstrap
- local backend startup
- git initialization
- the first 5 Codex prompts
- commands to verify each step
- the recommended working loop after every Codex run

---

## 1. Unpack the repository

Create the project directory and unpack the prepared structure into it.

```bash
mkdir kw-studio
cd kw-studio
unzip /path/to/kw_studio_ideal_structure.zip
```

If the archive is already in the current directory:

```bash
unzip kw_studio_ideal_structure.zip
```

---

## 2. Verify the unpacked structure

From the repository root:

```bash
find . -maxdepth 3 | sort
```

You should see at least:

```text
./.env.example
./.gitignore
./AGENTS.md
./Makefile
./README.md
./README.start-here.md
./docker-compose.yml
./requirements.txt
./backend
./backend/app
./backend/app/main.py
./backend/app/core
./backend/app/core/config.py
./backend/app/api
./backend/app/api/routes
./backend/app/api/routes/health.py
./backend/tests
./backend/tests/test_health.py
./docs
./docs/product-spec.md
./docs/roadmap.md
./docs/issue-pack.md
./frontend
./infra
./skills
./storage
./tools
```

---

## 3. Prepare local environment

### 3.1 Create `.env`

```bash
cp .env.example .env
```

### 3.2 Create virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.3 Install dependencies

```bash
make install
```

### 3.4 Create storage directories

```bash
make create-dirs
```

---

## 4. Run local checks before Codex

### 4.1 Run tests

```bash
make test
```

### 4.2 Check backend compilation

```bash
python -m compileall backend
```

### 4.3 Start backend

```bash
make run
```

### 4.4 Check health route

In another terminal:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 5. Optional Docker startup

If you want to run with Docker:

```bash
cp .env.example .env
docker compose up
```

Health check:

```bash
curl http://localhost:8000/health
```

Notes:
- backend should answer immediately
- frontend is still a placeholder until Codex scaffolds it
- postgres should start successfully

---

## 6. Initialize git

From repository root:

```bash
git init
git add .
git commit -m "bootstrap kw-studio structure"
```

If the repo already exists:

```bash
git add .
git commit -m "add kw-studio initial bootstrap"
```

---

## 7. Before starting Codex

Make sure these files exist and are readable:

- `AGENTS.md`
- `README.md`
- `README.start-here.md`
- `docs/product-spec.md`
- `docs/roadmap.md`
- `docs/issue-pack.md`

These are the files Codex should read first.

---

## 8. General Codex working rules

For every run:

1. Work from the repository root.
2. Ask Codex to read `AGENTS.md` and the relevant docs first.
3. Only give one narrow batch of issues at a time.
4. Require explicit checks at the end.
5. Review the diff before committing.

Recommended validation after each Codex run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If frontend changed:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

---

## 9. Prompt 1 — Bootstrap structure + backend health

Use this in Codex as the first implementation prompt.

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

### After Prompt 1, run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If all is good:

```bash
git add .
git commit -m "implement issue 001 and 002"
```

---

## 10. Prompt 2 — Frontend workspace shell

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

### After Prompt 2, run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
cd frontend && npm run lint && npm run build && cd ..
```

If all is good:

```bash
git add .
git commit -m "implement issue 003 frontend shell"
```

---

## 11. Prompt 3 — Core models + storage abstractions

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

### After Prompt 3, run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If all is good:

```bash
git add .
git commit -m "implement issue 004 and 005 models and storage"
```

---

## 12. Prompt 4 — Sessions, uploads, tasks API

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

### After Prompt 4, run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If all is good:

```bash
git add .
git commit -m "implement issue 006 sessions uploads tasks api"
```

---

## 13. Prompt 5 — Artifact API + orchestrator skeleton

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

### After Prompt 5, run:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If all is good:

```bash
git add .
git commit -m "implement issue 007 and 008 artifacts and orchestrator skeleton"
```

---

## 14. Recommended branch strategy

Use one branch per prompt batch.

Examples:

```bash
git checkout -b feat/issue-001-002
git checkout -b feat/issue-003
git checkout -b feat/issue-004-005
git checkout -b feat/issue-006
git checkout -b feat/issue-007-008
```

This keeps review and rollback simple.

---

## 15. What Codex should NOT do

Unless explicitly asked, Codex should not:

- convert the modular monolith into microservices
- delete bootstrap files
- expose browser runtime as a public MVP feature
- replace the architecture with a radically different stack
- add large infrastructure systems not required by the current issue
- mix runtime internals directly into API route files

These rules are already aligned with `AGENTS.md`, but it is still worth enforcing during review.

---

## 16. Safe review loop after each Codex run

Use this loop every time:

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If frontend changed:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

Then review:
- changed files
- whether acceptance criteria are met
- whether Codex respected `AGENTS.md`
- whether any extra scope was added

Only then commit.

---

## 17. Minimum success state after the first 5 runs

After the first 5 Codex runs, the repo should have:

- working backend health route
- initialized frontend workspace shell
- core backend domain model structure
- local storage abstraction
- sessions / uploads / tasks API
- artifact API
- orchestrator skeleton

At that point, the project is ready for the next stage:
- DOCX service MVP
- worker skeleton
- then PDF / data / slides flows

---

## 18. Short version

If you want the shortest practical order:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
make create-dirs
make test
make run
```

Then:

1. run Prompt 1
2. verify and commit
3. run Prompt 2
4. verify and commit
5. run Prompt 3
6. verify and commit
7. run Prompt 4
8. verify and commit
9. run Prompt 5
10. verify and commit

That is the cleanest path to a strong Codex-assisted KW Studio foundation.
