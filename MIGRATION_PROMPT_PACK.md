# MIGRATION_PROMPT_PACK.md

## Prompt M1 — Inventory and migration plan

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- docs/issue-pack.md
- README.start-here.md

A legacy codebase exists in the reference branch/repository `kernel_clean`.

Task:
Create a migration inventory and plan for selected legacy code that should be adapted into the new KW Studio architecture.

Legacy areas to inspect:
- jupyter kernel runtime
- kernel server
- browser runtime
- docx skill assets
- pdf skill assets
- slides prompt/tool assets if relevant

Target locations in the new project:
- backend/app/runtime/kernel/
- backend/app/runtime/browser/
- skills/docx/
- skills/pdf/
- backend/app/services/docx_service/
- backend/app/services/pdf_service/
- backend/app/services/slides_service/prompts/

Goals:
- identify which legacy files are reusable
- identify which ones are reference-only
- identify which ones need refactoring before migration
- propose a phased migration map
- create a migration document under docs/, for example docs/legacy-migration-plan.md

Constraints:
- do not blindly copy legacy code into production paths
- preserve the modular monolith architecture
- keep browser runtime internal-only
- separate runtime code from service/business logic
- do not break the current bootstrap or health route

Acceptance criteria:
- a clear migration inventory document is created
- files/classes/modules are mapped from legacy to new target locations
- risky legacy pieces are explicitly marked
- follow-up migration phases are proposed
- pytest -q still passes
- python -m compileall backend still passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- inspected legacy areas
- new migration document path
- changed files
- commands run
- test results
```

---

## Prompt M2 — Migrate kernel runtime foundation

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/legacy-migration-plan.md

Task:
Migrate the legacy kernel runtime foundation from `kernel_clean` into the new KW Studio runtime structure.

Legacy focus:
- jupyter kernel runtime code
- kernel server control-plane code

Target locations:
- backend/app/runtime/kernel/kernel_runtime.py
- backend/app/runtime/kernel/kernel_server.py
- backend/app/runtime/kernel/kernel_bootstrap.py
- backend/app/runtime/kernel/kernel_inspector.py

Goals:
- adapt legacy code into the new runtime layout
- keep the current backend bootstrap working
- avoid import-time side effects
- preserve health route behavior
- keep the migration incremental

Constraints:
- do not dump legacy files in raw form
- split responsibilities where reasonable
- keep FastAPI API routes separate from runtime internals
- keep public behavior minimal for now
- do not expose sensitive debug endpoints by default
- add smoke tests for migrated kernel runtime behavior

Acceptance criteria:
- runtime kernel code exists in the new target paths
- current backend still starts
- legacy kernel logic is adapted to the new architecture
- no import-time kernel startup side effects remain
- smoke tests are added or updated
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- migrated modules
- architectural changes made
- tests added/updated
- commands run
- remaining TODOs
```

---

## Prompt M3 — Migrate browser runtime foundation

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/legacy-migration-plan.md

Task:
Migrate the legacy browser runtime from `kernel_clean` into the new KW Studio browser runtime structure.

Legacy focus:
- browser guard logic
- Playwright-based control
- CDP-based control
- browser monitoring and restart behavior

Target locations:
- backend/app/runtime/browser/browser_supervisor.py
- backend/app/runtime/browser/playwright_controller.py
- backend/app/runtime/browser/cdp_controller.py
- backend/app/runtime/browser/utils.py

Goals:
- split the legacy browser runtime into clear modules
- keep browser runtime internal-only
- preserve the existing backend bootstrap
- carry over only the pieces needed for internal browser-assisted workflows

Constraints:
- do not expose browser automation as a public MVP feature
- do not keep unsafe defaults unless explicitly gated by env vars
- avoid sync network requests inside async code
- isolate legacy hacks behind optional helpers or env flags
- add smoke tests for basic startup/shutdown and internal helpers

Acceptance criteria:
- browser runtime code is present in the new target structure
- major legacy responsibilities are separated into controller/supervisor layers
- unsafe defaults are reduced or env-gated
- smoke tests are added or updated
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- migrated browser modules
- safety changes
- tests added/updated
- commands run
- remaining TODOs
```

---

## Prompt M4 — Migrate DOCX and PDF skills into service-aligned structure

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/legacy-migration-plan.md

Task:
Migrate selected legacy DOCX and PDF skill assets from `kernel_clean` into the new KW Studio structure.

Legacy focus:
- legacy docx skill assets and libraries
- legacy pdf skill assets and libraries

Target locations:
- skills/docx/
- skills/pdf/
- backend/app/services/docx_service/
- backend/app/services/pdf_service/

Goals:
- preserve reusable domain logic
- separate reusable skill assets from backend service wrappers
- create service entrypoints that align with the new architecture
- keep migration incremental and testable

Constraints:
- do not dump all legacy content blindly
- keep service modules thin and explicit
- move low-level skill logic under skills/
- move orchestration/service wrappers under backend/app/services/
- add or adapt tests for the migrated pieces
- preserve current project structure and bootstrap behavior

Acceptance criteria:
- selected DOCX skill logic is available under skills/docx and service wrappers
- selected PDF skill logic is available under skills/pdf and service wrappers
- clear service entrypoints exist for future orchestrator integration
- at least minimal smoke or unit coverage exists for migrated paths
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- migrated assets and wrappers
- tests added/updated
- commands run
- remaining TODOs
```

---

## Prompt M5 — Wire migrated pieces into orchestrator-safe interfaces

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/legacy-migration-plan.md

Task:
Integrate the migrated legacy runtime and service foundations into orchestrator-safe interfaces without implementing full end-to-end business workflows yet.

Focus:
- expose kernel runtime via clean internal interfaces
- expose browser runtime via internal-only interfaces
- create service-facing entrypoints for docx and pdf
- prepare orchestrator integration points
- keep the MVP modular monolith stable

Target areas:
- backend/app/orchestrator/
- backend/app/services/docx_service/
- backend/app/services/pdf_service/
- backend/app/runtime/kernel/
- backend/app/runtime/browser/

Goals:
- make migrated pieces usable from the new architecture
- keep boundaries clean
- avoid direct legacy-style coupling
- preserve current tests and bootstrap behavior

Constraints:
- do not implement full production workflows yet
- do not expose browser runtime publicly
- do not bypass service boundaries
- keep APIs thin and internal interfaces explicit
- add tests for wiring and basic integration behavior

Acceptance criteria:
- orchestrator-safe internal interfaces exist
- migrated runtime/service pieces can be referenced cleanly
- basic integration coverage exists
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend

At the end, summarize:
- integration points added
- changed files
- tests added/updated
- commands run
- remaining TODOs
```
