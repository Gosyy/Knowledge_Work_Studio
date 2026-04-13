# F_L_REVIEW_TACTICS.md

## Purpose

This document defines the review tactics for the **F–L implementation program** of KW Studio.

Use it after every Codex run to decide:
- whether the issue is actually complete
- whether scope drift happened
- whether the implementation is real or only nominal
- whether the patch should be accepted, rejected, or narrowed

This document is meant to be used together with:
- `F_L_PHASE_ISSUE_PACK.md`
- `F_L_ANTI_SCOPE_PROMPTS.md`
- `F_L_RUNBOOK.md`
- `DB_AND_STORAGE_ARCHITECTURE.md`

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
- Review the patch against the CURRENT branch state, not an assumed earlier snapshot.
- If a touched file had already changed in an earlier accepted issue, verify the patch against the live file shape.
- Reject or narrow patches that were clearly generated against stale file contents.
- Prefer additive changes over broad rewrites when a shared file has already drifted through accepted work.

### Patch-compatibility rules
- Treat patch applicability as a review concern, not merely a tooling concern.
- If a patch cannot apply cleanly because it assumes an outdated file shape, the patch should be narrowed or regenerated against the live branch state.
- Do not accept broad rewrites of shared files when the issue could be completed through a smaller compatible change.

### Pre-change verification rules
Before producing or reviewing a patch, verify:
- the current branch name
- current uncommitted state
- current diff/stat
- the live contents of every file the issue plans to modify

### Review-output rules
After coding, always:
- summarize only the requested issue
- explicitly confirm which neighboring issues were NOT implemented
- list commands run
- report test results
- call out blockers honestly if the issue could only be partially completed

### Minimum checks
Run exactly these checks unless the prompt explicitly adds more:
- `pytest -q`
- `python -m compileall backend`

If frontend changes:
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

---

# 1. Universal review rules

## Rule 1 — Review behavior, not just structure
Do not accept an issue only because:
- new files exist
- tests pass
- names look correct

Always ask whether the system behavior is real and aligned with the architecture.

## Rule 2 — Scope discipline is mandatory
A patch is not better just because it does more.
A patch is acceptable only if it implements the requested issue and avoids drifting into adjacent phases.

## Rule 3 — Real artifacts, not fake artifacts
Never accept:
- fake `.docx`
- fake `.pptx`
- misleading PDF behavior
- fake kernel/runtime behavior labeled as real execution

## Rule 4 — Approved truth layers must stay intact
The review must always check:
- Postgres remains the single metadata truth layer
- storage backend remains the binary truth layer
- SQLite does not silently remain a production truth path

## Rule 5 — One active provider model
The review must preserve:
- `LLM_PROVIDER=gigachat`
- no multi-provider runtime mixing
- no provider-specific leakage into business services

---

# 2. Standard command checklist

Run these before every issue:

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git diff --stat
git diff
```

Also inspect the live contents of every file the issue plans to modify.

Run these after every issue:

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

If artifact formats changed:
- generate a sample artifact
- inspect it manually
- confirm it opens in the expected software

If DB schema changed:
- inspect migrations
- inspect model/schema alignment
- inspect configuration

If runtime changed:
- inspect lifecycle
- inspect timeout/error behavior
- inspect traceability

---

# 3. Six mandatory review dimensions

Every issue must be reviewed across these six dimensions.

## A. Scope review
Ask:
- Did Codex implement only the requested issue?
- Did it touch neighboring issues?
- Did it introduce opportunistic refactors outside scope?
- Did it stay aligned with the current live branch state rather than an outdated earlier snapshot?

## B. Architecture review
Ask:
- Are modular monolith boundaries preserved?
- Are api / orchestrator / services / runtime / repositories / integrations still cleanly separated?
- Did provider-specific code leak into business services?
- Did storage truth and metadata truth remain separated?

## C. Truth-layer review
Ask:
- Is Postgres clearly the metadata truth?
- Is storage backend clearly the binary truth?
- Did SQLite remain anywhere as an accidental production truth path?

## D. Reality review
Ask:
- Is the new behavior real, or only nominal?
- Is the execution engine truly executing code?
- Are document/presentation outputs truly valid formats?

## E. Test review
Ask:
- Do tests pass?
- Were relevant tests added or updated?
- Do tests validate real behavior rather than placeholders?

## F. Hygiene review
Ask:
- Any generated garbage reintroduced?
- Any dead code or transitional duplication added?
- Any unexplained complexity added?

Only accept an issue if all six dimensions are acceptable.

---

# 4. Universal red flags

Reject or narrow the patch if any of these appear.

## Red flag 1 — Adjacent-phase scope drift
Examples:
- F2 starts implementing storage abstraction
- G1 starts redesigning providers
- H1 starts doing DOCX/PPTX work
- K1 starts adding UI/editor features

## Red flag 2 — Fake format outputs
Examples:
- text bytes saved as `.docx`
- pseudo-ZIP pretending to be `.pptx`
- non-PDF output labeled as PDF

## Red flag 3 — Fake execution behavior
Examples:
- helper marker path still acting as the “real engine”
- orchestration that claims execution but does not truly run code

## Red flag 4 — Hidden SQLite survival
Examples:
- SQLite still default in runtime config
- Postgres path exists but SQLite is silently preferred

## Red flag 5 — Provider leakage
Examples:
- direct GigaChat SDK/API calls scattered through services
- provider-specific logic bypassing `LLMProvider`

## Red flag 6 — Stale branch-state patching
Examples:
- patch hunks clearly target an older file shape
- shared wiring files are rewritten against stale context
- patch conflicts show the implementation was not regenerated against the live branch state

## Red flag 7 — Architecture inflation
Examples:
- giant abstractions added “for future use”
- broad refactors unrelated to the current issue
- new layers that make the system harder to follow

---

# 5. Universal acceptance gate

Accept an issue only if all are true:

1. the scope is correct
2. tests pass
3. backend compiles
4. approved truth layers are preserved
5. no fake artifacts are introduced
6. the implementation is genuinely real for the requested behavior
7. architecture is cleaner or more capable, not just larger
8. the patch is compatible with the current live branch state or has been honestly narrowed to fit it

---

# 6. Follow-up prompt if Codex drifts

Use this if Codex goes beyond scope:

```text
The previous attempt drifted outside scope.

Revert mentally to this issue only.
Implement only the requested issue.
Do not touch adjacent phases unless strictly required for compatibility.
Do not refactor unrelated modules.
Keep the patch narrow and reviewable.
Work against the current live branch state, not an earlier remembered file shape.

Before coding:
- list only the files strictly required for this issue
- explain why each file is necessary
- inspect the live contents of each target file before producing the patch

After coding:
- explicitly confirm which neighboring issues were NOT implemented
- summarize only this issue’s changes
```

Add this if Codex still tends to overreach:

```text
Do not opportunistically improve adjacent layers.
If blocked, stop at the smallest viable boundary and explain the blocker.
```

---

# 7. Issue-specific review tactics

## F1 — Repository hygiene cleanup
### Success criteria
- tracked `__pycache__` removed
- tracked `.pyc` / `.pyo` removed
- nested ZIP bundles removed from tracked tree
- temp patch/report artifacts removed from tracked tree
- `.gitignore` improved if needed

### Reject if
- source code or architecture changed
- useful docs/assets were deleted
- scope drift into DB/storage/runtime happened

### Key review question
Was this really just hygiene cleanup?

## F2 — Postgres becomes the single metadata truth layer
### Success criteria
- Postgres is clearly the production metadata backend
- SQLite is no longer the default truth path
- config is less ambiguous, not more
- metadata persistence clearly follows Postgres-first design

### Reject if
- SQLite still survives as production default
- storage/provider/runtime scope drift appears
- the patch becomes a giant unrelated DB rewrite

### Key review question
If I deploy this, is Postgres truly the single metadata truth layer?

## F3 — Storage backend abstraction
### Success criteria
- storage abstraction exists
- local filesystem backend exists
- remote object storage interface exists
- business logic does not assume only local direct paths

### Reject if
- Codex overbuilds remote storage infra
- storage logic leaks into routes/services as ad hoc code
- truth-layer boundaries become blurrier

### Key review question
Did this really separate binary truth from metadata truth?

## F4 — DB/storage schema for files, documents, presentations, lineage, derived content
### Success criteria
- schema/model support exists for:
  - `stored_files`
  - `documents`
  - `document_versions`
  - `presentations`
  - `presentation_versions`
  - `artifacts`
  - `artifact_sources`
  - `derived_contents`
- lineage exists
- versioning exists
- logical entities are separated from binary objects

### Reject if
- provenance is skipped
- logical and binary layers are merged carelessly
- only half the schema is implemented but presented as complete

### Key review question
Can this schema support real source-driven generation with provenance?

## F5 — LLM provider abstraction and GigaChat-first provider base
### Success criteria
- `LLMProvider` exists
- provider factory exists
- `Noop/FakeProvider` exists
- GigaChat-first provider bootstrap exists
- business services remain provider-agnostic
- shared DI/composition files are changed only as narrowly as required

### Reject if
- GigaChat calls leak directly into services
- multiple active providers appear in deployment logic
- abstraction is huge and unnecessary for this stage
- shared wiring files such as `api/dependencies.py` are broadly rewritten when a smaller additive change would satisfy F5

### Key review question
Can the app depend on a provider contract instead of provider-specific logic?

## G1 — Official execution API flow
### Success criteria
- official flow exists:
  - create task
  - execute task
  - get updated task
  - get artifact
- this is not only an internal helper path
- task types whose output pipelines are still fake or format-misleading are not silently promoted into the official public flow

### Reject if
- execution remains internal-only
- task lifecycle is still incomplete in the public flow
- Codex drifts into later execution or provider phases
- fake DOCX/PPTX/PDF behavior is exposed as if it were part of the official G1 runtime path

### Key review question
Can a client now really run the official end-to-end execution flow?

## G2 — Uploaded-source and stored-source task inputs
### Success criteria
- uploaded-source tasks work
- stored-source tasks work
- prompt-only tasks work
- provenance is recorded

### Reject if
- one of the three source modes is still nominal
- lineage is not persisted
- Codex starts redesigning the whole task model

### Key review question
Can users generate from uploads, existing stored materials, and prompt-only requests?

## G3 — Unify execution entrypoints and remove transitional duplication
### Success criteria
- one official execution entrypoint is evident
- transitional duplication is reduced or isolated
- the runtime flow is easier to understand

### Reject if
- another orchestration layer gets added
- changes are mostly cosmetic
- the system becomes harder to follow

### Key review question
Is the execution path objectively simpler after this change?

## H1 — Controlled Python execution engine
### Success criteria
- Python code is truly executed
- lifecycle is explicit
- timeout handling exists
- stdout/stderr capture exists
- cleanup exists

### Reject if
- fake helper-marker execution remains the main path
- execution still does not run real Python code
- timeout/isolation are absent

### Key review question
Is this now a real execution engine rather than a smarter-looking stub?

## H2 — Persist execution runs
### Success criteria
- `execution_runs` are persisted
- tasks link to execution traces
- enough metadata exists for debugging

### Reject if
- execution runs are only nominal
- traceability is too weak to debug failures
- unrelated runtime redesign sneaks in

### Key review question
Can I investigate a failed task from persisted execution data?

## H3 — Move data analysis onto the real engine
### Success criteria
- data analysis uses the real execution engine
- outputs become task results and/or artifacts
- helper-only analysis path is no longer the intended main path

### Reject if
- old fake path still acts as default
- analysis only pretends to use the real engine
- output traceability is weak

### Key review question
Does data analysis really depend on the new engine?

## I1 — Production-ready GigaChat provider
### Success criteria
- GigaChat provider is actually usable
- auth/config/timeouts/errors are handled cleanly
- deployment model remains single-provider active

### Reject if
- provider is only a stub
- business code depends directly on provider internals
- config/auth story is incomplete

### Key review question
Could this provider really be used in the approved intranet deployment?

## I2 — Provider-aware semantic workflows
### Success criteria
- classification/summarization/rewrite/outline go through `LLMProvider`
- `llm_runs` are persisted
- business services remain provider-agnostic

### Reject if
- provider logic leaks into services
- `llm_runs` are missing
- semantic calls are scattered ad hoc through the codebase

### Key review question
Is semantic behavior now routed through the provider layer cleanly?

## I3 — Prompt-only, uploaded-source, and stored-source semantic tasks
### Success criteria
- all three source modes support semantic workflows:
  - prompt-only
  - uploaded-source
  - stored-source

### Reject if
- one mode is only nominal
- provider behavior only works for one mode
- Codex drifts into J/K work

### Key review question
Are all three task input modes first-class semantic modes now?

## J1 — Real DOCX artifact pipeline
### Success criteria
- output is a real valid `.docx`
- artifact opens in real DOCX-capable software
- no text-bytes-with-docx-extension behavior remains
- lineage is preserved

### Reject if
- fake DOCX behavior remains
- MIME/extension fraud remains
- validity is assumed but not truly checked

### Key review question
Is the generated file truly a DOCX file?

## J2 — Honest PDF/report pipeline
### Success criteria
- no fake PDF remains
- output format is truthful and technically correct
- lineage is preserved

### Reject if
- file is labeled as PDF but is not actually PDF
- output semantics remain misleading
- implementation hides the format mismatch

### Key review question
Does the output format honestly match the real artifact?

## J3 — Reuse derived content for document/report generation
### Success criteria
- `derived_contents` are reused
- repeated reparsing is reduced
- generation paths benefit from stored extracted content

### Reject if
- derived content exists but is not truly used
- repeated generation still reparses unnecessarily by default

### Key review question
Does the system now genuinely reuse extracted source content?

## K1 — Valid PPTX generator
### Success criteria
- output is a real valid `.pptx`
- no pseudo-zip or text-based fake deck remains
- artifact opens correctly in target viewers

### Reject if
- fake PPTX behavior remains
- tests pass without proving package validity
- Codex drifts into advanced slide UX/editor work

### Key review question
Is the generated file truly a valid presentation package?

## K2 — Outline-first source-aware presentation generation
### Success criteria
- outline-first generation is real
- prompt-only, uploaded, and stored sources are supported
- provenance is stored
- output remains valid PPTX

### Reject if
- source-aware generation is nominal
- provenance is weak or missing
- valid PPTX output regresses

### Key review question
Can the system now build a new real presentation from existing system materials?

## L1 — Clear composition root
### Success criteria
- composition/bootstrap wiring is explicit
- provider/repository/storage/runtime/service wiring is understandable
- accidental dependency bottlenecks are reduced

### Reject if
- only superficial renaming happened
- hidden composition bottlenecks remain
- business logic was rewritten under the cover of wiring cleanup

### Key review question
Is the application assembly now explicitly understandable?

## L2 — Unify orchestration layers
### Success criteria
- duplicate/transitional orchestration surfaces are removed or isolated
- official runtime flow is clear

### Reject if
- another orchestration layer gets added
- simplification is cosmetic only
- execution flow regresses

### Key review question
Is orchestration now clearer and less transitional?

## L3 — Deployment hardening for offline intranet
### Success criteria
- configuration matches:
  - offline intranet
  - remote Postgres
  - remote storage
  - GigaChat-only deployment
- health/readiness/deployment docs exist
- secrets/config handling is safer

### Reject if
- public-internet assumptions remain
- deployment is still only half-documented
- provider fallback violates the approved architecture

### Key review question
Could this be deployed in the approved intranet architecture without architectural contradictions?

---

# 8. Minimum acceptance checklist

Do not accept any F–L issue unless all are true:
- scope is correct
- tests pass
- backend compiles
- architecture still matches approved rules
- no fake format outputs are introduced
- no forbidden truth-layer drift is introduced
- the implementation is genuinely real for the requested behavior

---

# 9. Final operational rule

If the result is:
- narrow
- honest
- real
- testable
- architecturally clean

→ accept it

If the result is:
- broad
- clever but slippery
- adjacent-phase heavy
- nominal rather than real

→ reject it, narrow it, and rerun with the anti-scope prompt
