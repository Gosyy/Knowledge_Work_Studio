# F_L_ANTI_SCOPE_PROMPTS.md

## How to use this file

- Run **one issue at a time**.
- Paste exactly one prompt into Codex.
- Do not merge adjacent issues unless explicitly approved.
- These prompts are written to prevent Codex from drifting away from the requested scope.
- Each prompt requires:
  - a pre-change file plan
  - narrow implementation
  - exact checks
  - explicit non-implementation confirmation for neighboring issues

---

## Prompt F1 — Repository hygiene cleanup

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- START_HERE_INDEX.md

Implement Issue F1 only.

Issue F1 scope:
Clean the repository and remove tracked generated garbage and transitional packaging artifacts.

Hard scope boundaries:
- Do NOT implement F2 or any later issue.
- Do NOT change database logic.
- Do NOT change storage logic.
- Do NOT change providers.
- Do NOT change execution/runtime behavior.
- Do NOT redesign the repository structure.

Allowed changes:
- tracked cache/artifact cleanup
- `.gitignore`
- tiny documentation updates only if needed to explain cleanup policy

Acceptance criteria:
- no tracked `__pycache__` remains
- no tracked `.pyc` remains
- no tracked nested bootstrap ZIP bundles remain in the working repository tree
- `.gitignore` is strengthened if necessary
- tests still pass

Before coding:
- list the exact files or tracked artifacts you will remove or change
- explain why each is required for F1

After coding:
- summarize only F1-related changes
- explicitly confirm that F2/F3/F4/F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that F1 cannot be completed without significant work beyond F1, stop at the smallest viable boundary, implement only the F1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt F2 — Postgres becomes the single metadata truth layer

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- SQL_DRAFT_SCHEMA_V1.sql
- F_L_PHASE_ISSUE_PACK.md

Implement Issue F2 only.

Issue F2 scope:
Make Postgres the only production metadata truth layer and remove SQLite as the default runtime truth path.

Hard scope boundaries:
- Do NOT implement F3 or later issues.
- Do NOT add full storage backend abstraction here.
- Do NOT add provider work here.
- Do NOT redesign unrelated service logic.
- Do NOT change frontend.

Allowed changes:
- repository/runtime metadata backend wiring
- Postgres repository implementations or default selection
- config/settings needed for Postgres-first runtime
- minimal migration/bootstrap work strictly required for F2
- tests directly needed for F2

Acceptance criteria:
- Postgres-backed metadata path is the default runtime path
- SQLite is not the production truth layer
- config clearly reflects Postgres-first architecture
- tests validate the intended behavior

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for F2

After coding:
- summarize only F2-related changes
- explicitly confirm that F1/F3/F4/F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that F2 cannot be completed without significant work beyond F2, stop at the smallest viable boundary, implement only the F2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt F3 — Storage backend abstraction and storage truth model

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue F3 only.

Issue F3 scope:
Introduce storage backend abstraction and make binary storage independent from metadata storage.

Hard scope boundaries:
- Do NOT implement F4 or later issues.
- Do NOT redesign all artifact behavior.
- Do NOT introduce remote provider logic.
- Do NOT change frontend.
- Do NOT redesign Postgres schema beyond what F3 strictly requires.

Allowed changes:
- storage interfaces
- local filesystem backend
- remote object storage interface skeleton
- metadata fields/wiring strictly needed for storage backend references
- tests directly needed for F3

Acceptance criteria:
- binary files are stored through a storage backend abstraction
- business logic no longer assumes only direct local paths
- deterministic storage key strategy exists
- metadata can reference backend, key, and URI

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for F3

After coding:
- summarize only F3-related changes
- explicitly confirm that F4/F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that F3 cannot be completed without significant work beyond F3, stop at the smallest viable boundary, implement only the F3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt F4 — DB/storage schema for files, documents, presentations, lineage, derived content

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- SQL_DRAFT_SCHEMA_V1.sql
- F_L_PHASE_ISSUE_PACK.md

Implement Issue F4 only.

Issue F4 scope:
Implement the approved schema model for stored files, logical documents, logical presentations, versions, artifacts, lineage, and derived content.

Hard scope boundaries:
- Do NOT implement F5 or later issues.
- Do NOT implement provider integration here.
- Do NOT implement execution engine changes here.
- Do NOT change frontend.
- Do NOT redesign unrelated task execution behavior.

Allowed changes:
- Postgres schema/migrations/models
- repositories/mappers directly related to the approved schema
- tests directly needed for F4

Acceptance criteria:
- source files and generated files are represented in Postgres
- documents and presentations have logical entities and versioning
- artifacts can point to lineage sources
- derived content storage exists
- schema matches the architecture document closely

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for F4

After coding:
- summarize only F4-related changes
- explicitly confirm that F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that F4 cannot be completed without significant work beyond F4, stop at the smallest viable boundary, implement only the F4-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt F5 — LLM provider abstraction and GigaChat-first provider base

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue F5 only.

Issue F5 scope:
Introduce provider abstraction, provider factory, test-safe provider path, and initial GigaChat-first provider base.

Hard scope boundaries:
- Do NOT implement G-phase or later issues.
- Do NOT spread provider-specific code through services.
- Do NOT fully implement all semantic workflows here.
- Do NOT change frontend.
- Do NOT add multi-provider runtime mixing.

Allowed changes:
- provider interfaces
- provider result models
- provider factory
- Noop/Fake provider
- GigaChat provider bootstrap/skeleton
- settings/config wiring directly needed for F5
- tests directly needed for F5

Acceptance criteria:
- business code can depend on `LLMProvider`
- `LLM_PROVIDER=gigachat` is supported
- test-safe provider exists
- GigaChat bootstrap/config path exists

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for F5

After coding:
- summarize only F5-related changes
- explicitly confirm that G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that F5 cannot be completed without significant work beyond F5, stop at the smallest viable boundary, implement only the F5-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt G1 — Official execution API flow

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue G1 only.

Issue G1 scope:
Create the official end-to-end execution API:
- create task
- execute task
- get updated task
- get artifact

Hard scope boundaries:
- Do NOT implement G2 or later issues.
- Do NOT redesign all orchestration architecture.
- Do NOT change frontend unless API contract adjustments absolutely require it.
- Do NOT add deep provider semantics here.
- Do NOT add fake shortcut execution paths.

Allowed changes:
- task execution API routes/handlers
- service/orchestrator wiring strictly needed for the official flow
- persistence updates strictly needed for the official flow
- tests directly needed for G1

Acceptance criteria:
- task can be created
- task can be executed through the official API flow
- task status updates are visible
- artifact retrieval works through the official flow
- this is the main supported backend path

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for G1

After coding:
- summarize only G1-related changes
- explicitly confirm that G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that G1 cannot be completed without significant G2 or later work, stop at the smallest viable boundary, implement only the G1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt G2 — Uploaded-source and stored-source task inputs

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue G2 only.

Issue G2 scope:
Support uploaded sources, stored sources, and prompt-only mode in task execution.

Hard scope boundaries:
- Do NOT implement G3 or later issues.
- Do NOT redesign the whole task model.
- Do NOT add deep semantic provider behavior here.
- Do NOT change frontend unless API contract adjustments absolutely require it.

Allowed changes:
- source selection/request models
- task input handling
- lineage recording for sources
- tests directly needed for G2

Acceptance criteria:
- uploaded sources can be attached to tasks
- stored documents/presentations/files can be used as task sources
- prompt-only mode is supported
- provenance is persisted

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for G2

After coding:
- summarize only G2-related changes
- explicitly confirm that G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that G2 cannot be completed without significant G3 or later work, stop at the smallest viable boundary, implement only the G2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt G3 — Unify execution entrypoints and remove transitional duplication

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue G3 only.

Issue G3 scope:
Remove or isolate transitional execution surfaces and keep one evident official execution path.

Hard scope boundaries:
- Do NOT implement H or later issues.
- Do NOT redesign the whole orchestrator.
- Do NOT change frontend.
- Do NOT broaden the scope into provider or runtime redesign.

Allowed changes:
- execution entrypoints
- transitional/deprecated surfaces
- tests directly needed for G3

Acceptance criteria:
- one main execution entrypoint is evident
- transitional duplication is reduced or isolated
- official runtime flow is easier to follow

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for G3

After coding:
- summarize only G3-related changes
- explicitly confirm that H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that G3 cannot be completed without significant later-phase work, stop at the smallest viable boundary, implement only the G3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt H1 — Controlled Python execution engine

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue H1 only.

Issue H1 scope:
Implement a real controlled Python execution engine with explicit lifecycle, timeout, stdout/stderr/result capture, and cleanup behavior.

Hard scope boundaries:
- Do NOT implement H2 or later issues.
- Do NOT broaden this into a generic platform rewrite.
- Do NOT change frontend.
- Do NOT leave fake helper execution as the main path.

Allowed changes:
- execution engine modules
- runtime integration strictly needed for H1
- tests directly needed for H1

Acceptance criteria:
- Python code is truly executed through the engine
- stdout/stderr are captured
- timeouts/failures are handled
- lifecycle and cleanup are explicit
- fake helper-only execution is no longer the final intended path

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for H1

After coding:
- summarize only H1-related changes
- explicitly confirm that H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that H1 cannot be completed without significant H2 or later work, stop at the smallest viable boundary, implement only the H1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt H2 — Persist execution runs

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue H2 only.

Issue H2 scope:
Persist execution runs and integrate them with the task lifecycle.

Hard scope boundaries:
- Do NOT implement H3 or later issues.
- Do NOT redesign the engine architecture.
- Do NOT change frontend.

Allowed changes:
- execution run persistence
- task-to-execution tracing
- tests directly needed for H2

Acceptance criteria:
- execution runs are persisted
- tasks are linked to execution traces
- enough execution metadata exists for debugging

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for H2

After coding:
- summarize only H2-related changes
- explicitly confirm that H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that H2 cannot be completed without significant H3 or later work, stop at the smallest viable boundary, implement only the H2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt H3 — Move data analysis onto the real engine

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue H3 only.

Issue H3 scope:
Move data analysis onto the real Python execution engine.

Hard scope boundaries:
- Do NOT implement I or later issues.
- Do NOT broaden into unrelated document or slides work.
- Do NOT change frontend.
- Do NOT leave the old fake analysis path as the main path.

Allowed changes:
- data-analysis service/runtime integration
- engine-backed result handling
- tests directly needed for H3

Acceptance criteria:
- data analysis uses the real engine
- outputs can become task results and/or artifacts
- tests validate the real execution path

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for H3

After coding:
- summarize only H3-related changes
- explicitly confirm that I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that H3 cannot be completed without significant I or later work, stop at the smallest viable boundary, implement only the H3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt I1 — Production-ready GigaChat provider

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue I1 only.

Issue I1 scope:
Implement a production-ready GigaChat provider behind the provider abstraction.

Hard scope boundaries:
- Do NOT implement I2 or later issues.
- Do NOT spread GigaChat-specific code through business services.
- Do NOT add multiple active providers in deployment.
- Do NOT change frontend.

Allowed changes:
- GigaChat provider implementation
- auth/token/config handling
- provider normalization
- tests directly needed for I1

Acceptance criteria:
- GigaChat provider is usable as the active provider
- auth/config handling is production-oriented
- provider behavior is normalized behind the provider interface

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for I1

After coding:
- summarize only I1-related changes
- explicitly confirm that I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that I1 cannot be completed without significant I2 or later work, stop at the smallest viable boundary, implement only the I1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt I2 — Provider-aware semantic workflows

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue I2 only.

Issue I2 scope:
Use the provider layer for classification, summarization, rewriting, and outline generation.

Hard scope boundaries:
- Do NOT implement I3 or later issues.
- Do NOT directly couple services to provider-specific APIs.
- Do NOT change frontend.
- Do NOT redesign all workflows.

Allowed changes:
- orchestrator/service semantic workflow integration through `LLMProvider`
- `llm_runs`
- tests directly needed for I2

Acceptance criteria:
- semantic tasks use GigaChat through the provider abstraction
- `llm_runs` are persisted
- service code does not directly depend on provider-specific APIs

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for I2

After coding:
- summarize only I2-related changes
- explicitly confirm that I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that I2 cannot be completed without significant I3 or later work, stop at the smallest viable boundary, implement only the I2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt I3 — Prompt-only, uploaded-source, and stored-source semantic tasks

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue I3 only.

Issue I3 scope:
Support semantic workflows through the provider layer across all three input modes:
- prompt-only
- uploaded-source
- stored-source

Hard scope boundaries:
- Do NOT implement J or later issues.
- Do NOT redesign the provider architecture.
- Do NOT change frontend.

Allowed changes:
- provider-aware task input handling
- tests directly needed for I3

Acceptance criteria:
- semantic flows work in all three supported generation modes

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for I3

After coding:
- summarize only I3-related changes
- explicitly confirm that J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that I3 cannot be completed without significant J or later work, stop at the smallest viable boundary, implement only the I3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt J1 — Real DOCX artifact pipeline

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue J1 only.

Issue J1 scope:
Implement a real valid DOCX artifact pipeline.

Hard scope boundaries:
- Do NOT implement J2 or later issues.
- Do NOT accept text bytes disguised as DOCX.
- Do NOT change frontend.
- Do NOT redesign unrelated provider flows.

Allowed changes:
- DOCX builder/pipeline
- service integration strictly needed for real DOCX generation
- tests directly needed for J1

Acceptance criteria:
- `.docx` output is a real valid DOCX file
- no fake DOCX output behavior remains
- artifact is downloadable
- source lineage is preserved

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for J1

After coding:
- summarize only J1-related changes
- explicitly confirm that J2/J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that J1 cannot be completed without significant J2 or later work, stop at the smallest viable boundary, implement only the J1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt J2 — Honest PDF/report pipeline

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue J2 only.

Issue J2 scope:
Implement an honest PDF/report output pipeline with technically correct output semantics.

Hard scope boundaries:
- Do NOT implement J3 or later issues.
- Do NOT claim PDF if the output is not truly PDF.
- Do NOT change frontend.
- Do NOT redesign unrelated generation flows.

Allowed changes:
- PDF/report pipeline
- service integration strictly needed for honest output
- tests directly needed for J2

Acceptance criteria:
- no fake PDF behavior remains
- output format is truthful and technically correct
- lineage is preserved

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for J2

After coding:
- summarize only J2-related changes
- explicitly confirm that J3/K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that J2 cannot be completed without significant J3 or later work, stop at the smallest viable boundary, implement only the J2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt J3 — Reuse derived content for document/report generation

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue J3 only.

Issue J3 scope:
Reuse `derived_contents` so repeated generation does not repeatedly reparse the same sources.

Hard scope boundaries:
- Do NOT implement K or later issues.
- Do NOT redesign the whole source ingestion layer.
- Do NOT change frontend.

Allowed changes:
- derived content reuse logic
- tests directly needed for J3

Acceptance criteria:
- generation flows can reuse extracted content
- repeated parsing work is reduced through the approved metadata model

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for J3

After coding:
- summarize only J3-related changes
- explicitly confirm that K1/K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that J3 cannot be completed without significant K or later work, stop at the smallest viable boundary, implement only the J3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt K1 — Valid PPTX generator

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue K1 only.

Issue K1 scope:
Implement a real valid PPTX generator.

Hard scope boundaries:
- Do NOT implement K2 or later issues.
- Do NOT accept pseudo-PPTX ZIP/text outputs.
- Do NOT change frontend.
- Do NOT add advanced editor/template-marketplace features.

Allowed changes:
- PPTX builder/pipeline
- service integration strictly needed for real PPTX output
- tests directly needed for K1

Acceptance criteria:
- `.pptx` output is a real valid PPTX file
- no fake PPTX output behavior remains
- downloadable artifact opens correctly in target viewers

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for K1

After coding:
- summarize only K1-related changes
- explicitly confirm that K2/L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that K1 cannot be completed without significant K2 or later work, stop at the smallest viable boundary, implement only the K1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt K2 — Outline-first source-aware presentation generation

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue K2 only.

Issue K2 scope:
Build outline-first source-aware presentation generation using prompt-only, uploaded, and stored sources.

Hard scope boundaries:
- Do NOT implement L or later issues.
- Do NOT redesign K1.
- Do NOT add advanced slide product features.
- Do NOT change frontend.

Allowed changes:
- outline-first presentation generation flow
- provenance-aware source handling for PPTX generation
- tests directly needed for K2

Acceptance criteria:
- outline-first flow is real
- existing presentations/documents/files can be used as sources
- provenance is stored
- resulting PPTX remains valid

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for K2

After coding:
- summarize only K2-related changes
- explicitly confirm that L1/L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that K2 cannot be completed without significant L or later work, stop at the smallest viable boundary, implement only the K2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt L1 — Clear composition root

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue L1 only.

Issue L1 scope:
Create a clear composition root for providers, repositories, storage backends, execution engine, and services.

Hard scope boundaries:
- Do NOT implement L2 or L3.
- Do NOT redesign business logic.
- Do NOT change frontend.

Allowed changes:
- composition/bootstrap wiring
- dependency injection entrypoints
- tests directly needed for L1

Acceptance criteria:
- composition is explicit
- the app no longer hides most wiring in accidental bottlenecks such as a bloated dependencies module

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for L1

After coding:
- summarize only L1-related changes
- explicitly confirm that L2/L3 were not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that L1 cannot be completed without significant L2 or L3 work, stop at the smallest viable boundary, implement only the L1-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt L2 — Unify orchestration layers

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md

Implement Issue L2 only.

Issue L2 scope:
Unify orchestration layers and remove transitional surfaces after the main runtime path is already real.

Hard scope boundaries:
- Do NOT implement L3.
- Do NOT redesign the entire product.
- Do NOT change frontend.

Allowed changes:
- orchestrator cleanup
- removal/isolation of transitional surfaces
- tests directly needed for L2

Acceptance criteria:
- duplicate/transitional orchestration paths are removed or isolated
- official runtime flow is clear

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for L2

After coding:
- summarize only L2-related changes
- explicitly confirm that L3 was not implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that L2 cannot be completed without significant L3 work, stop at the smallest viable boundary, implement only the L2-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```

---

## Prompt L3 — Deployment hardening for offline intranet

```text
Work from the repository root.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- START_HERE_INDEX.md

Implement Issue L3 only.

Issue L3 scope:
Harden deployment for:
- offline intranet mode
- remote Postgres
- remote storage
- GigaChat-only provider
- secrets/config safety

Hard scope boundaries:
- Do NOT redesign business workflows.
- Do NOT change frontend unless configuration contracts require it.
- Do NOT add public-internet features.

Allowed changes:
- config cleanup
- health/readiness checks
- deployment docs
- secrets/config handling
- remote infrastructure safety wiring
- tests directly needed for L3

Acceptance criteria:
- approved deployment model is explicitly supported
- config aligns with offline intranet + GigaChat + Postgres + storage backend architecture
- deployment hardening is documented

Before coding:
- list the exact files you plan to change
- explain why each file is necessary for L3

After coding:
- summarize only L3-related changes
- explicitly confirm that no work outside L3 was implemented
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that L3 cannot be completed without significant work beyond L3, stop at the smallest viable boundary, implement only the L3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```
