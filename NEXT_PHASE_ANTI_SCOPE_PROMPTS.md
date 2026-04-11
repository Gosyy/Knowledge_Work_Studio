# NEXT_PHASE_ANTI_SCOPE_PROMPTS.md

## Prompt A1 — Persistent repositories

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue A1 only.

Issue A1 scope:
Replace in-memory repositories with persistent implementations for:
- sessions
- tasks
- artifacts
- uploaded files

You may also do the minimum required wiring needed to make those persistent repositories the default app path.

Hard scope boundaries:
- Do NOT implement Issue A2.
- Do NOT add a migration framework or migration baseline.
- Do NOT change frontend files.
- Do NOT implement artifact download.
- Do NOT implement orchestrator execution changes.
- Do NOT deepen DOCX, PDF, data, or PPTX workflows.
- Do NOT refactor unrelated modules just because they could be improved.
- Do NOT introduce microservices.
- Do NOT rewrite the architecture.

Allowed changes:
- repository implementations
- repository interfaces if strictly necessary
- minimal database/integration wiring strictly required for A1
- minimal dependency/bootstrap/container wiring strictly required for A1
- tests directly needed for A1
- tiny doc updates only if setup or behavior changes

Prefer:
- small, reviewable patch
- stable interfaces
- minimal invasive changes
- backward-compatible API behavior

Persistence requirements:
- sessions persist across process restart
- tasks persist across process restart
- artifacts persist across process restart
- uploaded file metadata persists across process restart

Acceptance criteria:
- persistent repositories exist and are used by default app wiring
- current API behavior is preserved
- persistence works for sessions, tasks, artifacts, and uploaded file metadata
- tests cover the new persistence behavior
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain in 5 bullets or fewer why each file is necessary for A1

After coding:
- summarize only A1-related changes
- explicitly confirm that A2/B1/B2/C1/C2/D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that A1 cannot be completed without significant A2 work, stop at the smallest viable boundary, implement only the A1-safe subset, and explain exactly what remains blocked by A2.
```

## Prompt A2 — DB bootstrap and migration baseline

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue A2 only.

Issue A2 scope:
Create a minimal database bootstrap and migration baseline structure.

This task is about:
- database settings wiring
- database initialization path
- migration baseline structure
- documentation for local DB startup and migration flow

Hard scope boundaries:
- Do NOT re-implement A1.
- Do NOT redesign repository interfaces unless strictly required for startup.
- Do NOT implement artifact storage changes.
- Do NOT implement artifact download.
- Do NOT implement task execution lifecycle.
- Do NOT implement orchestrator execution wiring.
- Do NOT deepen DOCX/PDF/data/PPTX workflows.
- Do NOT touch frontend unless documentation or env references absolutely require it.
- Do NOT add enterprise-grade infra or excessive migration tooling.

Allowed changes:
- database bootstrap modules
- config/settings updates
- minimal startup wiring
- scripts/migrations structure
- documentation updates
- tests directly needed for A2

Prefer:
- the smallest migration baseline that is maintainable
- explicit docs over framework complexity
- compatibility with the A1 persistence path
- minimal invasive changes

Acceptance criteria:
- DB bootstrap exists
- local DB setup is documented
- migration baseline structure exists
- app startup works with persistence enabled
- tests still pass
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for A2

After coding:
- summarize only A2-related changes
- explicitly confirm that A1/B1/B2/C1/C2/D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that A2 cannot be completed without significant work beyond A2, stop at the smallest viable boundary, implement only the A2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

## Prompt B1 — Real storage-backed artifacts

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue B1 only.

Issue B1 scope:
Turn artifacts into real storage-backed outputs instead of metadata-only objects.

This task is about:
- extending artifact metadata with file/storage details
- saving artifact content through the storage abstraction
- linking artifact metadata to actual stored content

Hard scope boundaries:
- Do NOT implement B2.
- Do NOT add download endpoints in this task.
- Do NOT change frontend.
- Do NOT implement orchestrator execution changes.
- Do NOT deepen DOCX/PDF/data/PPTX workflows.
- Do NOT redesign persistence beyond what artifact storage strictly needs.
- Do NOT bypass the storage abstraction.
- Do NOT introduce browser or runtime changes.

Allowed changes:
- artifact domain model
- artifact service
- storage abstraction/integration pieces strictly needed for artifact persistence
- repository/model updates strictly needed for artifact metadata
- tests directly needed for B1

Prefer:
- storage-backed artifact lifecycle
- deterministic file naming
- backward-compatible artifact metadata expansion
- minimal API surface change

Acceptance criteria:
- artifact creation writes a real file or managed placeholder file
- artifact metadata references actual stored content
- artifact retrieval path is deterministic
- tests cover artifact creation and lookup
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for B1

After coding:
- summarize only B1-related changes
- explicitly confirm that B2/C1/C2/D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that B1 cannot be completed without significant B2 work, stop at the smallest viable boundary, implement only the B1-safe subset, and explain exactly what remains blocked by B2.
```

## Prompt B2 — Artifact download API

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue B2 only.

Issue B2 scope:
Add artifact download API on top of the storage-backed artifact system.

This task is about:
- artifact metadata fetch
- artifact file download response
- correct content type and filename handling
- tests for success and failure paths

Hard scope boundaries:
- Do NOT rework B1 beyond what is strictly required for API compatibility.
- Do NOT implement orchestrator execution changes.
- Do NOT deepen any service workflow.
- Do NOT change frontend.
- Do NOT redesign storage.
- Do NOT introduce new artifact generation semantics.
- Do NOT implement PPTX or other feature work.

Allowed changes:
- artifact API routes
- artifact service methods needed for download
- response handling
- tests directly needed for B2

Prefer:
- thin route handlers
- service-driven artifact lookup
- clear error handling
- minimal interface changes

Acceptance criteria:
- artifact metadata endpoint works
- artifact download endpoint returns actual file content
- invalid artifact IDs return correct errors
- tests cover both metadata and download flow
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for B2

After coding:
- summarize only B2-related changes
- explicitly confirm that C1/C2/D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that B2 cannot be completed without significant work beyond B2, stop at the smallest viable boundary, implement only the B2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

## Prompt C1 — Task execution lifecycle

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue C1 only.

Issue C1 scope:
Introduce a real task execution lifecycle:
- pending
- running
- succeeded
- failed

This task is about:
- lifecycle transitions
- execution state persistence
- structured task result data
- minimal execution coordination path

Hard scope boundaries:
- Do NOT implement C2.
- Do NOT wire orchestrator to all services yet.
- Do NOT deepen DOCX/PDF/data/PPTX workflows.
- Do NOT change frontend.
- Do NOT add browser-heavy behavior.
- Do NOT introduce a large workflow engine.
- Do NOT redesign persistence or artifacts unless strictly required for lifecycle state.

Allowed changes:
- task domain models
- repositories for task state persistence
- application/coordinator logic for lifecycle transitions
- tests directly needed for C1

Prefer:
- explicit lifecycle transitions
- small, testable execution path
- transport-free core execution logic
- minimal invasive changes

Acceptance criteria:
- task can move through pending/running/succeeded/failed
- success and failure states are persisted
- execution result is captured in a structured way
- tests cover lifecycle transitions
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for C1

After coding:
- summarize only C1-related changes
- explicitly confirm that C2/D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that C1 cannot be completed without significant C2 work, stop at the smallest viable boundary, implement only the C1-safe subset, and explain exactly what remains blocked by C2.
```

## Prompt C2 — Orchestrator to service execution wiring

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue C2 only.

Issue C2 scope:
Wire orchestrator to service execution for supported task types:
- docx_edit
- pdf_summary
- data_analysis
- slides_generate (stub execution path allowed)

This task is about:
- routing task types to service handlers
- stable execution contracts between orchestrator and services
- persisting task outputs and artifact references

Hard scope boundaries:
- Do NOT redesign the orchestrator architecture.
- Do NOT deepen DOCX/PDF/data/PPTX service internals in this task.
- Do NOT implement full browser runtime behavior.
- Do NOT change frontend.
- Do NOT turn this into a workflow engine framework.
- Do NOT rewrite task lifecycle semantics from C1.

Allowed changes:
- orchestrator wiring
- service execution contracts
- result composition and artifact reference handling
- integration tests directly needed for C2

Prefer:
- thin orchestration
- domain logic staying inside services
- clear internal interfaces
- testable integration flow

Acceptance criteria:
- orchestrator selects the correct service path
- service results can produce task result plus artifact reference
- basic integration tests exist
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for C2

After coding:
- summarize only C2-related changes
- explicitly confirm that D1/D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that C2 cannot be completed without significant D-phase work, stop at the smallest viable boundary, implement only the C2-safe subset, and explain exactly what remains blocked and which D issue it belongs to.
```

## Prompt D1 — Deep DOCX integration

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue D1 only.

Issue D1 scope:
Deepen DOCX workflow using migrated skill assets and replace placeholder text replacement with at least one real DOCX transformation path.

This task is about:
- integrating migrated DOCX skill logic into docx_service
- supporting one meaningful document workflow
- producing a real downloadable artifact through the existing artifact pipeline

Hard scope boundaries:
- Do NOT implement D2 or D3.
- Do NOT deepen PDF workflows.
- Do NOT change PPTX logic.
- Do NOT redesign orchestrator architecture.
- Do NOT change frontend.
- Do NOT expose low-level skill internals directly through routes.
- Do NOT attempt multiple DOCX workflows if one strong one is enough.

Allowed changes:
- skills/docx
- backend/app/services/docx_service
- tests directly needed for DOCX integration
- minimal orchestrator/service contract adjustments strictly needed for this workflow

Prefer:
- one strong end-to-end DOCX slice
- service wrapper staying explicit
- low-level logic remaining under skills/docx
- downloadable artifact as the end state

Acceptance criteria:
- DOCX service uses migrated skill assets
- at least one real DOCX workflow works end-to-end
- resulting artifact is downloadable
- tests cover service behavior
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for D1

After coding:
- summarize only D1-related changes
- explicitly confirm that D2/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that D1 cannot be completed without significant work beyond D1, stop at the smallest viable boundary, implement only the D1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

## Prompt D2 — Deep PDF integration

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue D2 only.

Issue D2 scope:
Deepen PDF workflow using migrated skill assets and replace placeholder summarization with a real extraction and summary path.

This task is about:
- integrating migrated PDF skill logic into pdf_service
- extracting content from PDF
- building summary output from extracted content
- persisting outputs through the artifact pipeline where appropriate

Hard scope boundaries:
- Do NOT implement D1 or D3.
- Do NOT change PPTX logic.
- Do NOT change frontend.
- Do NOT introduce browser-heavy PDF flows unless absolutely required.
- Do NOT redesign orchestrator architecture.
- Do NOT deepen DOCX or data flows.

Allowed changes:
- skills/pdf
- backend/app/services/pdf_service
- tests directly needed for PDF integration
- minimal orchestration/service contract updates strictly needed for this PDF path

Prefer:
- thin service wrapper
- low-level logic under skills/pdf
- one strong extraction+summary path
- artifact pipeline reuse instead of new output plumbing

Acceptance criteria:
- PDF service uses migrated PDF skill assets
- extraction plus summary works end-to-end
- output is persisted when applicable
- tests cover extraction and summary behavior
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for D2

After coding:
- summarize only D2-related changes
- explicitly confirm that D1/D3/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that D2 cannot be completed without significant work beyond D2, stop at the smallest viable boundary, implement only the D2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

## Prompt D3 — Real kernel-backed data analysis

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue D3 only.

Issue D3 scope:
Connect data analysis to a real kernel execution path and support a minimal real analysis flow for CSV/XLSX.

This task is about:
- a minimal real execution path through kernel runtime
- structured result text
- optional chart/data artifacts
- internal runtime integration only

Hard scope boundaries:
- Do NOT implement D1 or D2.
- Do NOT deepen PPTX workflows.
- Do NOT expose runtime internals through the API layer.
- Do NOT implement full notebook/session UX.
- Do NOT change frontend.
- Do NOT reintroduce import-time side effects.
- Do NOT broaden this into a generic execution platform rewrite.

Allowed changes:
- backend/app/runtime/kernel
- backend/app/services/data_service
- orchestrator wiring strictly needed for data analysis
- runtime/service tests directly needed for D3

Prefer:
- explicit runtime lifecycle
- minimal real execution path
- narrow testable data-analysis slice
- internal interfaces over public runtime expansion

Acceptance criteria:
- data analysis invokes a real execution path
- results can be persisted as task output and/or artifact
- runtime smoke tests exist
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for D3

After coding:
- summarize only D3-related changes
- explicitly confirm that D1/D2/E1/E2 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that D3 cannot be completed without significant E-phase work or broader runtime redesign, stop at the smallest viable boundary, implement only the D3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

## Prompt E1 — Slides service MVP execution path

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue E1 only.

Issue E1 scope:
Add the first real slides service execution path that generates and stores a simple PPTX artifact.

This task is about:
- slides service execution entrypoint
- simple deck structure generation
- support for input from notes, summary text, or extracted source content
- PPTX artifact persistence

Hard scope boundaries:
- Do NOT implement E2.
- Do NOT build an advanced slide design system.
- Do NOT create a template marketplace.
- Do NOT add a complex visual editor.
- Do NOT add browser-heavy enhancement unless absolutely required.
- Do NOT redesign orchestrator architecture.
- Do NOT change unrelated DOCX/PDF/data flows.

Allowed changes:
- backend/app/services/slides_service
- minimal orchestrator wiring needed for slides tasks
- artifact pipeline usage for PPTX
- tests directly needed for E1

Prefer:
- narrow PPTX MVP
- fixed template or minimal template system
- reliable artifact generation over visual sophistication
- end-to-end downloadable PPTX

Acceptance criteria:
- slides task can run through orchestrator
- a PPTX artifact is created and stored
- artifact can be downloaded
- tests cover the basic slides generation path
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for E1

After coding:
- summarize only E1-related changes
- explicitly confirm that E2 was not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that E1 cannot be completed without significant E2 work, stop at the smallest viable boundary, implement only the E1-safe subset, and explain exactly what remains blocked by E2.
```

## Prompt E2 — Outline-first slides generation

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md
- NEXT_PHASE_ISSUE_PACK.md

Implement Issue E2 only.

Issue E2 scope:
Add an outline-first step before deck generation and produce a 5–10 slide deck from outline.

This task is about:
- outline builder
- outline-to-deck generation
- deterministic enough output for tests
- artifact persistence for the resulting PPTX

Hard scope boundaries:
- Do NOT redesign E1.
- Do NOT add advanced design/layout engines.
- Do NOT add template marketplace features.
- Do NOT add browser-first layout generation.
- Do NOT change frontend.
- Do NOT expand into collaboration or editing UX.
- Do NOT redesign PPTX generation beyond what outline-first requires.

Allowed changes:
- backend/app/services/slides_service/outline.py
- backend/app/services/slides_service/generator.py
- minimal service/orchestrator changes strictly needed for outline-first flow
- tests directly needed for E2

Prefer:
- clear outline contract
- deterministic, testable generation
- small implementation
- reuse of existing PPTX artifact pipeline

Acceptance criteria:
- outline is generated before deck creation
- deck generation consumes outline cleanly
- resulting PPTX remains downloadable
- tests cover outline plus generation flow
- pytest -q passes
- python -m compileall backend passes

Before coding:
- briefly list the exact files you plan to change
- explain why each file is necessary for E2

After coding:
- summarize only E2-related changes
- explicitly confirm that no new work outside E2 was implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that E2 cannot be completed without significant work beyond E2, stop at the smallest viable boundary, implement only the E2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```
