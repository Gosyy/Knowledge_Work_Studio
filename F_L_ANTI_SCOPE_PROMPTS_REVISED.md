# F_L_ANTI_SCOPE_PROMPTS_REVISED.md

## Purpose

This file is the revised main prompt pack for **F–L**.
It takes the original `F_L_ANTI_SCOPE_PROMPTS.md` and incorporates the most important corrective review rules from `F_L_REVIEW_TACTICS.md`.

Use this file instead of the older main prompt pack when you want Codex to be constrained not only by issue scope, but also by:
- real behavior checks
- truth-layer discipline
- fake-artifact prevention
- provider-boundary discipline
- deployment-model discipline

---

## Global rules that apply to every F–L prompt

These rules are part of every issue below even if they are not repeated in full.

### Reality rules
- Do not ship nominal behavior in place of real behavior.
- Do not label fake outputs as real outputs.
- A `.docx` must be a real DOCX package.
- A `.pptx` must be a real PPTX package.
- If output is not truly PDF, do not label it PDF.

### Truth-layer rules
- Postgres is the single metadata truth layer.
- Storage backend is the binary truth layer.
- Do not keep SQLite as an accidental production truth path.

### Provider rules
- GigaChat is the only active deployment provider.
- Do not mix multiple providers in runtime behavior.
- Do not leak provider-specific code into business services.

### Scope rules
- Implement only the requested issue.
- Do not opportunistically improve adjacent layers.
- Do not redesign the entire architecture under the cover of a narrow issue.
- Keep the patch narrow and reviewable.

### Current-branch-state rules
- Work against the current checked-out branch state, not an assumed earlier snapshot.
- Before planning, inspect the current branch contents of every file you may change.
- Do not generate a patch against stale file contents.
- If a previously modified file has drifted from the earlier expected shape, re-plan against the live file instead of forcing the old patch shape.
- Prefer additive changes over broad rewrites when a file has already been modified by earlier accepted work.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

### Patch-generation rules
- If the output is intended to be applied as a patch, base it on the current file contents of the branch, not on a remembered earlier version.
- Do not modify a previously changed file unless it is strictly required for the current issue.
- If the issue can be completed without touching a drift-prone file, prefer that narrower path.
- If a patch would likely conflict with accepted earlier changes, narrow the patch instead of rewriting the file.

### Review-output rules
After coding, always:
- summarize only the requested issue
- explicitly confirm which neighboring issues were NOT implemented
- list commands run
- report test results
- call out blockers honestly if the issue could only be partially completed

### Pre-change verification rules
Before coding, always:
- run `git status --short`
- run `git rev-parse --abbrev-ref HEAD`
- run `git diff --stat`
- run `git diff`
- inspect the current contents of the files you plan to change
- confirm whether each target file has changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch

### Minimum checks
Run exactly these checks unless the prompt explicitly adds more:
- `pytest -q`
- `python -m compileall backend`

If frontend changes:
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

---

## Prompt F1 — Repository hygiene cleanup

```text
Work from the repository root.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- START_HERE_INDEX.md
- F_L_REVIEW_TACTICS.md

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
- no tracked temporary patch/report artifacts remain in the working tree
- `.gitignore` is strengthened if necessary
- tests still pass

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- SQL_DRAFT_SCHEMA_V1.sql
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue F2 only.

Issue F2 scope:
Make Postgres the only production metadata truth layer and remove SQLite as the default runtime truth path.

Hard scope boundaries:
- Do NOT implement F3 or later issues.
- Do NOT add full storage backend abstraction here.
- Do NOT add provider work here.
- Do NOT redesign unrelated service logic.
- Do NOT change frontend.

Reality / truth-layer constraints:
- Postgres must become the actual default production metadata path.
- SQLite must not survive as an accidental or hidden production truth path.
- Do not present config as Postgres-first if runtime still silently prefers SQLite.

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for F2

After coding:
- summarize only F2-related changes
- explicitly confirm that F1/F3/F4/F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm whether SQLite remains anywhere in the runtime path and why
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue F3 only.

Issue F3 scope:
Introduce storage backend abstraction and make binary storage independent from metadata storage.

Hard scope boundaries:
- Do NOT implement F4 or later issues.
- Do NOT redesign all artifact behavior.
- Do NOT introduce remote provider logic.
- Do NOT change frontend.
- Do NOT redesign Postgres schema beyond what F3 strictly requires.

Truth-layer constraints:
- storage backend must become the binary truth layer abstraction
- business logic must not hardcode local-only path assumptions
- do not blur metadata truth and binary truth into one layer

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for F3

After coding:
- summarize only F3-related changes
- explicitly confirm that F4/F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how metadata truth and binary truth remain separated
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- SQL_DRAFT_SCHEMA_V1.sql
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue F4 only.

Issue F4 scope:
Implement the approved schema model for stored files, logical documents, logical presentations, versions, artifacts, lineage, and derived content.

Hard scope boundaries:
- Do NOT implement F5 or later issues.
- Do NOT implement provider integration here.
- Do NOT implement execution engine changes here.
- Do NOT change frontend.
- Do NOT redesign unrelated task execution behavior.

Schema reality constraints:
- lineage must be real, not nominal
- versioning must be real, not implied
- logical documents/presentations must stay distinct from binary files
- `stored_files` must remain the canonical file registry concept

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for F4

After coding:
- summarize only F4-related changes
- explicitly confirm that F5/G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how lineage and versioning are represented
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue F5 only.

Issue F5 scope:
Introduce provider abstraction, provider factory, test-safe provider path, and initial GigaChat-first provider base.

Hard scope boundaries:
- Do NOT implement G-phase or later issues.
- Do NOT spread provider-specific code through services.
- Do NOT fully implement all semantic workflows here.
- Do NOT change frontend.
- Do NOT add multi-provider runtime mixing.

Provider constraints:
- GigaChat is the only active deployment provider
- business code must depend on `LLMProvider`, not provider-specific APIs
- do not leak provider-specific details into DOCX/PDF/slides/data services

Allowed changes:
- provider interfaces
- provider result models
- provider factory
- Noop/Fake provider
- GigaChat provider bootstrap/skeleton
- settings/config wiring directly needed for F5
- tests directly needed for F5

Additional F5 patch-safety constraints:
- Do not rewrite shared DI/composition files broadly if F5 can be completed with narrower additive changes.
- If `api/dependencies.py` or another shared wiring file has already been modified by an accepted patch, prefer adding the smallest required function or import only.
- Do not reformat or reorganize shared wiring files unless strictly required for F5 acceptance criteria.

Acceptance criteria:
- business code can depend on `LLMProvider`
- `LLM_PROVIDER=gigachat` is supported
- test-safe provider exists
- GigaChat bootstrap/config path exists

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for F5

After coding:
- summarize only F5-related changes
- explicitly confirm that G1/G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how provider leakage into business services was prevented
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

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

Reality constraints:
- this must become a real supported public path, not just a wrapped internal helper
- task lifecycle updates must be observable through the official flow
- artifact retrieval must be part of the official flow
- do not expose an official execution path for task types whose output pipeline is still fake or format-misleading
- if some task types still depend on fake DOCX/PPTX/PDF behavior, either keep them out of the official G1 path or fail them honestly with an explicit not-yet-supported response
- G1 must not silently promote unfinished J/K-format behavior into the official public execution flow

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for G1

After coding:
- summarize only G1-related changes
- explicitly confirm that G2/G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what the single official execution flow now is
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue G2 only.

Issue G2 scope:
Support uploaded sources, stored sources, and prompt-only mode in task execution.

Hard scope boundaries:
- Do NOT implement G3 or later issues.
- Do NOT redesign the whole task model.
- Do NOT add deep semantic provider behavior here.
- Do NOT change frontend unless API contract adjustments absolutely require it.

Reality constraints:
- all three modes must be real:
  - uploaded-source
  - stored-source
  - prompt-only
- provenance must be persisted, not implied
- stored-source mode must not be nominal only

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for G2

After coding:
- summarize only G2-related changes
- explicitly confirm that G3/H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how each of the three source modes is supported
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue G3 only.

Issue G3 scope:
Remove or isolate transitional execution surfaces and keep one evident official execution path.

Hard scope boundaries:
- Do NOT implement H or later issues.
- Do NOT redesign the whole orchestrator.
- Do NOT change frontend.
- Do NOT broaden the scope into provider or runtime redesign.

Reality constraints:
- one main execution path must become easier to identify
- duplication must be reduced in real code flow, not only renamed

Allowed changes:
- execution entrypoints
- transitional/deprecated surfaces
- tests directly needed for G3

Acceptance criteria:
- one main execution entrypoint is evident
- transitional duplication is reduced or isolated
- official runtime flow is easier to follow

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for G3

After coding:
- summarize only G3-related changes
- explicitly confirm that H1/H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what execution surfaces were removed, isolated, or deprecated
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue H1 only.

Issue H1 scope:
Implement a real controlled Python execution engine with explicit lifecycle, timeout, stdout/stderr/result capture, and cleanup behavior.

Hard scope boundaries:
- Do NOT implement H2 or later issues.
- Do NOT broaden this into a generic platform rewrite.
- Do NOT change frontend.
- Do NOT leave fake helper execution as the main path.

Reality constraints:
- Python code must truly execute
- helper-marker-only pseudo-execution must not remain the intended main path
- lifecycle, timeout, and cleanup must be explicit

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for H1

After coding:
- summarize only H1-related changes
- explicitly confirm that H2/H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what makes this a real engine instead of the prior fake/helper path
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue H2 only.

Issue H2 scope:
Persist execution runs and integrate them with the task lifecycle.

Hard scope boundaries:
- Do NOT implement H3 or later issues.
- Do NOT redesign the engine architecture.
- Do NOT change frontend.

Reality constraints:
- execution runs must be truly persisted and linked to tasks
- stored metadata must be useful for debugging, not merely decorative

Allowed changes:
- execution run persistence
- task-to-execution tracing
- tests directly needed for H2

Acceptance criteria:
- execution runs are persisted
- tasks are linked to execution traces
- enough execution metadata exists for debugging

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for H2

After coding:
- summarize only H2-related changes
- explicitly confirm that H3/I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what debugging/traceability data is now persisted
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue H3 only.

Issue H3 scope:
Move data analysis onto the real Python execution engine.

Hard scope boundaries:
- Do NOT implement I or later issues.
- Do NOT broaden into unrelated document or slides work.
- Do NOT change frontend.
- Do NOT leave the old fake analysis path as the main path.

Reality constraints:
- data analysis must truly depend on the real engine
- outputs must become task results and/or artifacts through the real path
- the old helper path must not remain the intended default

Allowed changes:
- data-analysis service/runtime integration
- engine-backed result handling
- tests directly needed for H3

Acceptance criteria:
- data analysis uses the real engine
- outputs can become task results and/or artifacts
- tests validate the real execution path

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for H3

After coding:
- summarize only H3-related changes
- explicitly confirm that I1/I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how the old fake analysis path was replaced or demoted
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue I1 only.

Issue I1 scope:
Implement a production-ready GigaChat provider behind the provider abstraction.

Hard scope boundaries:
- Do NOT implement I2 or later issues.
- Do NOT spread GigaChat-specific code through business services.
- Do NOT add multiple active providers in deployment.
- Do NOT change frontend.

Provider/deployment constraints:
- GigaChat must remain the only active deployment provider
- provider internals must stay behind `LLMProvider`
- auth/config/timeouts/errors must be production-oriented, not demo-only

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for I1

After coding:
- summarize only I1-related changes
- explicitly confirm that I2/I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how provider-specific details were kept out of business services
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue I2 only.

Issue I2 scope:
Use the provider layer for classification, summarization, rewriting, and outline generation.

Hard scope boundaries:
- Do NOT implement I3 or later issues.
- Do NOT directly couple services to provider-specific APIs.
- Do NOT change frontend.
- Do NOT redesign all workflows.

Provider/reality constraints:
- semantic workflows must go through `LLMProvider`
- `llm_runs` must be persisted
- business services must remain provider-agnostic

Allowed changes:
- orchestrator/service semantic workflow integration through `LLMProvider`
- `llm_runs`
- tests directly needed for I2

Acceptance criteria:
- semantic tasks use GigaChat through the provider abstraction
- `llm_runs` are persisted
- service code does not directly depend on provider-specific APIs

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for I2

After coding:
- summarize only I2-related changes
- explicitly confirm that I3/J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how `llm_runs` are recorded and how provider leakage was prevented
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

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

Reality constraints:
- all three task input modes must be real semantic modes
- no mode may remain nominal-only

Allowed changes:
- provider-aware task input handling
- tests directly needed for I3

Acceptance criteria:
- semantic flows work in all three supported generation modes

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for I3

After coding:
- summarize only I3-related changes
- explicitly confirm that J1/J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm how prompt-only, uploaded-source, and stored-source semantic flows are each supported
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue J1 only.

Issue J1 scope:
Implement a real valid DOCX artifact pipeline.

Hard scope boundaries:
- Do NOT implement J2 or later issues.
- Do NOT accept text bytes disguised as DOCX.
- Do NOT change frontend.
- Do NOT redesign unrelated provider flows.

Reality constraints:
- `.docx` output must be a real valid DOCX package
- no text-bytes-with-docx-extension behavior may remain
- lineage must be preserved

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for J1

After coding:
- summarize only J1-related changes
- explicitly confirm that J2/J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what makes the output a real DOCX package
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue J2 only.

Issue J2 scope:
Implement an honest PDF/report output pipeline with technically correct output semantics.

Hard scope boundaries:
- Do NOT implement J3 or later issues.
- Do NOT claim PDF if the output is not truly PDF.
- Do NOT change frontend.
- Do NOT redesign unrelated generation flows.

Reality constraints:
- output labeling must match actual output format
- no fake PDF behavior may remain
- lineage must be preserved

Allowed changes:
- PDF/report pipeline
- service integration strictly needed for honest output
- tests directly needed for J2

Acceptance criteria:
- no fake PDF behavior remains
- output format is truthful and technically correct
- lineage is preserved

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for J2

After coding:
- summarize only J2-related changes
- explicitly confirm that J3/K1/K2/L1/L2/L3 were not implemented
- explicitly confirm what output format is produced and why it is truthful
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue J3 only.

Issue J3 scope:
Reuse `derived_contents` so repeated generation does not repeatedly reparse the same sources.

Hard scope boundaries:
- Do NOT implement K or later issues.
- Do NOT redesign the whole source ingestion layer.
- Do NOT change frontend.

Reality constraints:
- derived content reuse must be real and visible in generation flow
- reparsing should be reduced by design, not only by naming

Allowed changes:
- derived content reuse logic
- tests directly needed for J3

Acceptance criteria:
- generation flows can reuse extracted content
- repeated parsing work is reduced through the approved metadata model

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for J3

After coding:
- summarize only J3-related changes
- explicitly confirm that K1/K2/L1/L2/L3 were not implemented
- explicitly confirm where `derived_contents` is reused in generation paths
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue K1 only.

Issue K1 scope:
Implement a real valid PPTX generator.

Hard scope boundaries:
- Do NOT implement K2 or later issues.
- Do NOT accept pseudo-PPTX ZIP/text outputs.
- Do NOT change frontend.
- Do NOT add advanced editor/template-marketplace features.

Reality constraints:
- `.pptx` output must be a real valid PPTX package
- pseudo-ZIP/text deck behavior must be eliminated
- output must be viewer-openable

Allowed changes:
- PPTX builder/pipeline
- service integration strictly needed for real PPTX output
- tests directly needed for K1

Acceptance criteria:
- `.pptx` output is a real valid PPTX file
- no fake PPTX output behavior remains
- downloadable artifact opens correctly in target viewers

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for K1

After coding:
- summarize only K1-related changes
- explicitly confirm that K2/L1/L2/L3 were not implemented
- explicitly confirm what makes the output a real PPTX package
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue K2 only.

Issue K2 scope:
Build outline-first source-aware presentation generation using prompt-only, uploaded, and stored sources.

Hard scope boundaries:
- Do NOT implement L or later issues.
- Do NOT redesign K1.
- Do NOT add advanced slide product features.
- Do NOT change frontend.

Reality constraints:
- outline-first flow must be real
- prompt-only / uploaded / stored sources must all be supported
- provenance must be recorded
- output must remain a valid PPTX

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for K2

After coding:
- summarize only K2-related changes
- explicitly confirm that L1/L2/L3 were not implemented
- explicitly confirm how prompt-only, uploaded, and stored sources are used in PPTX generation
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue L1 only.

Issue L1 scope:
Create a clear composition root for providers, repositories, storage backends, execution engine, and services.

Hard scope boundaries:
- Do NOT implement L2 or L3.
- Do NOT redesign business logic.
- Do NOT change frontend.

Reality constraints:
- composition must become explicitly understandable
- accidental wiring bottlenecks must be reduced in reality, not just renamed

Allowed changes:
- composition/bootstrap wiring
- dependency injection entrypoints
- tests directly needed for L1

Acceptance criteria:
- composition is explicit
- the app no longer hides most wiring in accidental bottlenecks such as a bloated dependencies module

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for L1

After coding:
- summarize only L1-related changes
- explicitly confirm that L2/L3 were not implemented
- explicitly confirm where the new composition root is and what wiring moved there
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md

Implement Issue L2 only.

Issue L2 scope:
Unify orchestration layers and remove transitional surfaces after the main runtime path is already real.

Hard scope boundaries:
- Do NOT implement L3.
- Do NOT redesign the entire product.
- Do NOT change frontend.

Reality constraints:
- official runtime flow must become clearer in real code paths
- duplicate/transitional orchestration surfaces must actually be reduced

Allowed changes:
- orchestrator cleanup
- removal/isolation of transitional surfaces
- tests directly needed for L2

Acceptance criteria:
- duplicate/transitional orchestration paths are removed or isolated
- official runtime flow is clear

Before coding:
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for L2

After coding:
- summarize only L2-related changes
- explicitly confirm that L3 was not implemented
- explicitly confirm which orchestration surfaces were unified, removed, or isolated
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

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites when a shared file was already modified by an accepted earlier issue.
- If patch compatibility is uncertain, stop and report the exact conflicting file(s) before producing the patch.

Read these files first and use them as the only planning context:
- AGENTS.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- START_HERE_INDEX.md
- F_L_REVIEW_TACTICS.md

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

Deployment constraints:
- deployment assumptions must match the approved architecture exactly
- no public-internet dependency may remain in the deployment profile
- no hidden provider fallback may violate GigaChat-only deployment

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
- inspect the current contents of each target file
- confirm whether each target file changed since the previous accepted issue
- if a target file has drifted, restate the plan against the live file shape before writing the patch
- list the exact files you plan to change
- explain why each file is necessary for L3

After coding:
- summarize only L3-related changes
- explicitly confirm that no work outside L3 was implemented
- explicitly confirm how the final deployment profile matches offline intranet + remote Postgres + remote storage + GigaChat-only architecture
- list commands run
- report test results

Run exactly these checks:
- pytest -q
- python -m compileall backend

If you find that L3 cannot be completed without significant work beyond L3, stop at the smallest viable boundary, implement only the L3-safe subset, and explain exactly what remains blocked and which later issue or phase it belongs to.
```
