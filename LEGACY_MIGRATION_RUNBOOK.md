# LEGACY_MIGRATION_RUNBOOK.md

## Purpose

This runbook describes the recommended migration workflow for bringing selected legacy code from the `kernel_clean` codebase into the new **KW Studio** repository.

It focuses on a safe, incremental migration of:

- kernel runtime
- kernel server / control plane
- browser runtime
- DOCX skill assets
- PDF skill assets

This runbook assumes you have already completed the bootstrap phase of KW Studio and that the repository already contains the new modular-monolith structure.

---

## 1. Preconditions

Before starting legacy migration, make sure the new repository is already bootstrapped and working.

You should already have:
- unpacked `kw_studio_ideal_structure.zip`
- run the local backend successfully
- completed the initial Codex prompts 1–5
- committed those changes to git

### Required current state

From the repository root, these should pass:

```bash
pytest -q
python -m compileall backend
```

The backend health route should also work:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 2. Migration philosophy

The legacy code from `kernel_clean` should **not** be copied blindly into the new project.

Instead, migration must follow these rules:

1. Inventory first, migrate second
2. Split responsibilities when moving runtime code
3. Keep the modular monolith boundaries intact
4. Do not expose internal browser runtime as a public MVP feature
5. Preserve the working bootstrap at every step
6. Add tests and smoke coverage as code moves

---

## 3. What is being migrated

### Runtime layer
Legacy source areas:
- Jupyter kernel runtime
- kernel server / runtime control plane
- browser guard / browser runtime

Target structure:
- `backend/app/runtime/kernel/`
- `backend/app/runtime/browser/`

### Skills and services
Legacy source areas:
- DOCX skill assets
- PDF skill assets

Target structure:
- `skills/docx/`
- `skills/pdf/`
- `backend/app/services/docx_service/`
- `backend/app/services/pdf_service/`

### Prompts and tool specs
If needed later:
- `prompts/slides.md`
- `tools/.../slides_generator...`

Target structure:
- `backend/app/services/slides_service/prompts/`
- `tools/tool_specs/`

---

## 4. Branch strategy

Use a dedicated branch for each migration prompt.

Recommended branch names:

```bash
git checkout -b feat/migration-inventory
git checkout -b feat/migrate-kernel-runtime
git checkout -b feat/migrate-browser-runtime
git checkout -b feat/migrate-docx-pdf-skills
git checkout -b feat/migration-integration
```

This makes the migration reviewable and reversible.

---

## 5. Baseline check before starting M1

From the repository root:

```bash
git status
pytest -q
python -m compileall backend
```

If frontend exists and is already scaffolded:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

You want a clean baseline before migration starts.

---

## 6. Migration Prompt M1 — Inventory and migration plan

### Goal
Inspect the legacy codebase and create a proper migration plan before moving any code.

### Prompt
Use **Prompt M1** from `MIGRATION_PROMPT_PACK.md`.

### Expected output
A document like:
- `docs/legacy-migration-plan.md`

That document should include:
- legacy file inventory
- risk classification
- source → target mapping
- migration phases
- files to reuse
- files to adapt
- files to leave as reference only

### Commands to run after M1

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

### What to review after M1
Check that:
- the migration plan document exists
- risky legacy areas are clearly flagged
- no production code was blindly copied yet
- bootstrap still works

### Commit after M1

```bash
git add .
git commit -m "add legacy migration inventory and plan"
```

---

## 7. Migration Prompt M2 — Kernel runtime foundation

### Goal
Move the legacy kernel runtime into the new runtime structure.

### Prompt
Use **Prompt M2** from `MIGRATION_PROMPT_PACK.md`.

### Target files
Typical target files include:
- `backend/app/runtime/kernel/kernel_runtime.py`
- `backend/app/runtime/kernel/kernel_server.py`
- `backend/app/runtime/kernel/kernel_bootstrap.py`
- `backend/app/runtime/kernel/kernel_inspector.py`

### Migration principles for M2
- no import-time side effects
- runtime logic separated from API concerns
- no overly broad public surface by default
- preserve health route and overall backend startup

### Commands to run after M2

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

Optional targeted run if routes changed:

```bash
make run
curl http://localhost:8000/health
```

### What to review after M2
Check that:
- kernel code is now in the new runtime path
- responsibilities are split or at least clearly staged for split
- no import-time startup side effects remain
- backend still starts
- tests were added or updated

### Commit after M2

```bash
git add .
git commit -m "migrate kernel runtime foundation"
```

---

## 8. Migration Prompt M3 — Browser runtime foundation

### Goal
Move and adapt the legacy browser runtime into the new browser runtime structure.

### Prompt
Use **Prompt M3** from `MIGRATION_PROMPT_PACK.md`.

### Target files
Typical target files include:
- `backend/app/runtime/browser/browser_supervisor.py`
- `backend/app/runtime/browser/playwright_controller.py`
- `backend/app/runtime/browser/cdp_controller.py`
- `backend/app/runtime/browser/utils.py`

### Migration principles for M3
- browser runtime remains internal-only
- keep unsafe defaults behind env flags
- avoid sync network calls inside async code
- isolate GUI hacks behind helpers or flags
- split controller and supervisor responsibilities

### Commands to run after M3

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If there are browser-runtime-specific smoke tests:

```bash
pytest -q backend/tests/runtime
```

### What to review after M3
Check that:
- browser code is not exposed as a public product feature
- runtime modules are separated cleanly
- dangerous defaults are reduced or env-gated
- smoke coverage exists for startup/shutdown or basic helpers
- the rest of the backend still compiles and tests pass

### Commit after M3

```bash
git add .
git commit -m "migrate browser runtime foundation"
```

---

## 9. Migration Prompt M4 — DOCX and PDF skills

### Goal
Move selected legacy DOCX and PDF skill assets into the new service-aligned structure.

### Prompt
Use **Prompt M4** from `MIGRATION_PROMPT_PACK.md`.

### Target locations
- `skills/docx/`
- `skills/pdf/`
- `backend/app/services/docx_service/`
- `backend/app/services/pdf_service/`

### Migration principles for M4
- low-level reusable logic goes under `skills/`
- service wrappers go under `backend/app/services/`
- do not mix raw legacy code directly into route handlers
- preserve or adapt tests where possible

### Commands to run after M4

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If tests were added under skills or services, run them explicitly too:

```bash
pytest -q backend/tests/services
```

### What to review after M4
Check that:
- migrated skill logic is organized under `skills/`
- service wrappers are thin and explicit
- no blind dump of the whole legacy tree happened
- test coverage was added or adapted
- backend still builds and test suite passes

### Commit after M4

```bash
git add .
git commit -m "migrate docx and pdf skill foundations"
```

---

## 10. Migration Prompt M5 — Integration into orchestrator-safe interfaces

### Goal
Wire the migrated runtime and service pieces into the new architecture through clean internal interfaces.

### Prompt
Use **Prompt M5** from `MIGRATION_PROMPT_PACK.md`.

### Focus areas
- orchestrator integration points
- runtime-facing internal interfaces
- service-facing entrypoints
- no full business workflows yet
- no public browser-runtime exposure

### Commands to run after M5

```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
```

If frontend changed unexpectedly:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

### What to review after M5
Check that:
- orchestrator can reference migrated pieces cleanly
- internal interfaces are explicit
- service boundaries are preserved
- bootstrap still works
- no legacy-style tight coupling was reintroduced

### Commit after M5

```bash
git add .
git commit -m "integrate migrated legacy foundations into new architecture"
```

---

## 11. Recommended review checklist after every migration prompt

Use this checklist after **every** M1–M5 step.

### Diff review
```bash
git diff --stat
git diff
```

### Backend validation
```bash
pytest -q
python -m compileall backend
```

### Optional runtime checks
If runtime files changed:

```bash
make run
curl http://localhost:8000/health
```

### Optional frontend checks
If frontend changed:

```bash
cd frontend
npm run lint
npm run build
cd ..
```

### Manual review questions
- Did Codex preserve the modular monolith?
- Did Codex avoid blind file dumping?
- Did Codex keep browser runtime internal-only?
- Did Codex preserve bootstrap stability?
- Did Codex add tests for the migrated piece?
- Did Codex separate runtime code from business/service code?

---

## 12. What to do if Codex migrates too much at once

If Codex attempts to move too much code in a single step:

1. stop and review the diff
2. reject or revert the oversized change
3. restate the prompt with narrower scope
4. force a single subsystem focus

Example correction prompt:

```text
The previous migration was too broad.

Please narrow the change to only the kernel runtime foundation.
Do not touch browser runtime, services, or frontend.
Preserve all existing passing tests.
Keep the patch small and reviewable.
```

---

## 13. What should not happen during legacy migration

Unless explicitly requested, migration should **not**:
- turn the product into microservices
- expose browser runtime publicly
- copy the legacy repository wholesale
- delete the new bootstrap structure
- bypass service or runtime boundaries
- mix raw legacy internals into API route modules
- break the current `/health` path or local run flow

---

## 14. Suggested end state after the migration pack

After M1–M5, the repository should have:

### Runtime
- kernel runtime foundation under `backend/app/runtime/kernel/`
- browser runtime foundation under `backend/app/runtime/browser/`

### Skills and services
- selected DOCX skill assets under `skills/docx/`
- selected PDF skill assets under `skills/pdf/`
- thin backend service wrappers for DOCX/PDF

### Integration
- orchestrator-safe internal interfaces
- smoke coverage for migrated foundations
- no broken bootstrap behavior

This is the point where the project is ready for the next stage:
- real DOCX workflow integration
- PDF workflow integration
- data-analysis runtime integration
- slides generation integration

---

## 15. Short version

If you want the shortest possible migration loop:

### Before each migration prompt
```bash
git checkout -b <new-branch-name>
pytest -q
python -m compileall backend
```

### Run one migration prompt
- M1
- M2
- M3
- M4
- M5

### After each migration prompt
```bash
git diff --stat
git diff
pytest -q
python -m compileall backend
git add .
git commit -m "<migration step>"
```

That is the safest and cleanest way to bring `kernel_clean` into the new KW Studio architecture.
