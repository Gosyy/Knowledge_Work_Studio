# F_L_PHASE_ISSUE_PACK.md

## F–L Phase Issue Pack — KW Studio

This issue pack defines the next major implementation program for KW Studio after the previous A1–E2 phase.

This phase is **not** a fresh greenfield roadmap. It is a corrective and forward-moving roadmap that must both:
1. fix the major architectural and product gaps found in the current codebase
2. move the system toward the approved deployment architecture:
   - offline intranet deployment
   - no public internet
   - remote access over LAN / VPN / bastion
   - **GigaChat as the only active LLM provider**
   - **Postgres as the single metadata truth layer**
   - storage backend as the binary truth layer
   - real Python execution engine
   - real DOCX / PDF / PPTX artifact pipelines

---

## Global corrective requirements

These are mandatory across F–L and are not optional:

1. **No fake `.docx` artifacts**
   - A `.docx` artifact must be a real valid DOCX package, not plain text bytes with a DOCX filename or MIME type.

2. **No fake `.pptx` artifacts**
   - A `.pptx` artifact must be a real valid PPTX package, not a placeholder ZIP or text-based pseudo-deck.

3. **No misleading PDF output**
   - Either produce a real PDF/report pipeline or clearly produce a non-PDF artifact such as `.txt`, `.md`, or `.html`. Do not claim PDF if the output is not truly PDF.

4. **No SQLite as production truth**
   - Postgres is the only metadata truth layer in the approved architecture.
   - SQLite transitional paths must not remain the default production path.

5. **No fake kernel runtime**
   - The data-analysis path must move toward a real Python execution engine.
   - Helper-only or marker-only fake execution must not remain the final solution.

6. **No scope drift**
   - Each issue must be implemented narrowly.
   - Do not redesign the whole architecture under the cover of one issue.

7. **No repo hygiene debt**
   - Repository cleanup is part of the program:
     - remove `__pycache__`
     - remove `.pyc`
     - remove nested ZIP artifacts from tracked tree
     - remove temporary patch/text artifacts from tracked tree

8. **No hidden lineage loss**
   - Generated artifacts must preserve source provenance.

---

## Approved deployment model

The implementation must support:

- app server on an internal network
- Postgres on a separate server
- storage backend local or remote
- remote user access over LAN/VPN
- GigaChat API access
- no dependency on public internet services for runtime behavior

---

## Phase F — Foundation cleanup, Postgres truth layer, storage truth model, provider base

### Issue F1 — Repository hygiene cleanup

#### Goal
Clean the repository and remove transitional or generated garbage from tracked code.

#### Scope
- remove `__pycache__`
- remove `.pyc`
- remove nested ZIP artifacts from tracked repository tree
- remove temporary patch/text artifacts that should not live in repo
- tighten `.gitignore` if needed

#### Acceptance criteria
- no generated Python cache artifacts remain tracked
- no bootstrap ZIP bundles remain tracked inside the working repository
- `.gitignore` protects against reintroducing this garbage
- tests still pass

---

### Issue F2 — Postgres becomes the single metadata truth layer

#### Goal
Replace SQLite as the default metadata runtime path and make Postgres the only production metadata truth layer.

#### Scope
- remove SQLite as the default repository backend
- implement Postgres-first repository path
- move session/task/artifact/upload metadata to Postgres-backed repositories
- align config with Postgres-first architecture
- remove config ambiguity between SQLite and Postgres

#### Acceptance criteria
- Postgres-backed repositories are the default runtime path
- SQLite is not the production truth layer
- metadata persists through Postgres only
- tests cover Postgres-backed behavior where practical
- startup/config clearly reflects the new truth layer

---

### Issue F3 — Introduce storage backend abstraction and storage truth model

#### Goal
Make binary storage independent from metadata storage.

#### Scope
- introduce `StorageBackend` abstraction
- support local filesystem backend first
- define remote object storage interface
- move file handling to storage backend contract
- align stored file metadata with `stored_files` model

#### Acceptance criteria
- application no longer assumes only direct local paths in business logic
- binary files are stored via storage backend abstraction
- metadata references storage backend + key + URI
- deterministic storage key patterns exist

---

### Issue F4 — Introduce DB/storage schema for files, documents, presentations, lineage, derived content

#### Goal
Implement the approved Postgres metadata model from `DB_AND_STORAGE_ARCHITECTURE.md`.

#### Scope
- `stored_files`
- `documents`
- `document_versions`
- `presentations`
- `presentation_versions`
- `artifacts`
- `artifact_sources`
- `derived_contents`
- necessary migrations/models/repositories

#### Acceptance criteria
- source files and generated files are represented in Postgres
- documents and presentations have logical entities plus versions
- artifacts can point to source lineage
- extracted content can be stored and reused
- schema is aligned with the architecture document

---

### Issue F5 — Introduce LLM provider abstraction and GigaChat-first provider base

#### Goal
Introduce provider abstraction without coupling business logic directly to one provider implementation.

#### Scope
- create `LLMProvider` interface
- create provider result models
- create provider factory
- implement `NoopProvider` / `FakeProvider` for tests
- implement initial `GigaChatProvider` bootstrap/skeleton
- wire settings for a single active provider

#### Constraints
- GigaChat is the only active provider in deployment
- other providers may exist in code but remain inactive by default
- do not spread provider-specific code through services

#### Acceptance criteria
- business code can depend on `LLMProvider`, not provider-specific APIs
- `LLM_PROVIDER=gigachat` is supported
- test-safe provider path exists
- GigaChat provider bootstrap/config path exists

---

## Phase G — Real execution API and source-aware task flow

### Issue G1 — Implement the official execution API flow

#### Goal
Create the official end-to-end backend flow:
- create task
- execute task
- get updated task
- get artifact

#### Scope
- public execution path
- task lifecycle persistence
- artifact result persistence
- integrate with Postgres-backed truth model
- make this the main supported flow, not an internal-only helper path

#### Acceptance criteria
- a task can be created
- a task can be executed
- task status updates are visible
- artifact retrieval works
- this is the official supported backend flow

---

### Issue G2 — Add uploaded-source and stored-source task input support

#### Goal
Support both user-uploaded sources and existing stored system sources in task execution.

#### Scope
- user may attach files to a task
- user may select already stored documents/presentations/files as task sources
- prompt-only tasks remain supported
- source provenance is recorded

#### Acceptance criteria
- tasks can use uploaded sources
- tasks can use stored sources
- tasks can use prompt-only mode
- artifact lineage records source provenance

---

### Issue G3 — Unify task execution entrypoints and remove transitional duplication

#### Goal
Reduce confusion between old coordinator/integration surfaces and the official execution path.

#### Scope
- identify and remove or deprecate transitional execution surfaces
- keep one main execution path
- preserve testability

#### Acceptance criteria
- one main execution entrypoint is evident
- transitional surfaces are removed, deprecated, or clearly isolated
- execution behavior is easier to follow

---

## Phase H — Real Python execution engine

### Issue H1 — Implement a controlled Python execution engine

#### Goal
Move from helper-style pseudo-execution to a real Python execution engine.

#### Scope
- controlled Python subprocess execution
- explicit lifecycle
- timeout handling
- stdout capture
- stderr capture
- structured result capture
- local temp file support
- cleanup behavior

#### Acceptance criteria
- Python code is truly executed through the engine
- execution runs are tracked
- stdout/stderr are captured
- timeouts/failures are handled
- helper-marker-only execution no longer defines the main path

---

### Issue H2 — Persist execution runs and integrate them with task lifecycle

#### Goal
Make execution traceable and operationally visible.

#### Scope
- implement `execution_runs`
- persist engine status/result metadata
- link execution runs to tasks
- expose enough data for debugging and operations

#### Acceptance criteria
- execution runs are persisted
- each task can be tied to execution traces
- operational debugging data exists

---

### Issue H3 — Move data analysis onto the real engine

#### Goal
Make data analysis use the real execution engine instead of a fake kernel-like helper path.

#### Scope
- CSV/XLSX analysis over the real engine
- text output and optional chart/data artifacts
- engine-backed result persistence

#### Acceptance criteria
- data analysis uses the real engine
- output can become task result and/or artifact
- tests validate the real execution path

---

## Phase I — Full GigaChat semantic integration

### Issue I1 — Implement production-ready GigaChat provider

#### Goal
Move from provider skeleton to a real usable GigaChat integration.

#### Scope
- auth/token flow
- model selection
- request/response normalization
- error handling
- timeout handling
- provider config for offline-intranet deployment

#### Acceptance criteria
- GigaChat provider can be used as the active runtime provider
- auth/config are properly handled
- provider behavior is normalized behind the provider interface

---

### Issue I2 — Introduce provider-aware semantic workflows

#### Goal
Use GigaChat for:
- classification
- summarization
- rewriting
- outline generation

#### Scope
- orchestrator semantic calls through provider abstraction
- log provider usage through `llm_runs`
- keep one active provider per deployment

#### Acceptance criteria
- semantic tasks use GigaChat through the provider layer
- `llm_runs` are persisted
- services do not directly depend on GigaChat SDK/API details

---

### Issue I3 — Support prompt-only, uploaded-source, and stored-source semantic tasks

#### Goal
Make the provider layer work consistently across all three generation modes.

#### Acceptance criteria
- provider-driven semantic flows work in:
  - prompt-only mode
  - uploaded-source mode
  - stored-source mode

---

## Phase J — Real DOCX and honest/real PDF pipelines

### Issue J1 — Implement a real DOCX artifact pipeline

#### Goal
Replace fake DOCX payload generation with a real valid DOCX pipeline.

#### Scope
- valid DOCX package generation
- preserve or transform structure
- support at least one meaningful document workflow
- use existing documents as sources where appropriate
- register output through storage + Postgres metadata

#### Acceptance criteria
- output `.docx` is a real valid DOCX file
- no text-bytes-with-docx-extension behavior remains
- artifact is downloadable
- source lineage is preserved

---

### Issue J2 — Implement an honest PDF/report pipeline

#### Goal
Replace misleading PDF semantics with either:
- a real PDF/report artifact path
or
- a clearly non-PDF report artifact path

#### Scope
- use existing documents/presentations/files as sources where appropriate
- extraction + summary + output pipeline
- output format must be honest and technically correct

#### Acceptance criteria
- no fake PDF behavior remains
- output format is truthful
- artifact lineage is preserved

---

### Issue J3 — Reuse derived content for document/report generation

#### Goal
Avoid reparsing the same source files repeatedly.

#### Scope
- use `derived_contents`
- normalize source content reuse across document/report generation

#### Acceptance criteria
- repeated generation can reuse extracted content
- derived content meaningfully reduces duplicated parsing work

---

## Phase K — Real PPTX MVP

### Issue K1 — Implement a valid PPTX generator

#### Goal
Replace pseudo-PPTX generation with a real valid PPTX pipeline.

#### Scope
- valid `.pptx` package generation
- deterministic builder
- downloadable artifact
- source-aware generation

#### Acceptance criteria
- output `.pptx` is a real valid PPTX file
- no fake ZIP/text pseudo-deck remains
- artifact is downloadable and opens correctly in target viewers

---

### Issue K2 — Implement outline-first source-aware presentation generation

#### Goal
Build new presentations from:
- prompt-only input
- uploaded source files
- existing documents
- existing presentations

#### Scope
- outline generation via provider
- deterministic slide assembly
- lineage-aware generation

#### Acceptance criteria
- outline-first flow is real
- existing presentations/documents can be used as sources
- provenance is stored
- output PPTX is valid

---

## Phase L — Composition cleanup and deployment hardening

### Issue L1 — Create a clear composition root

#### Goal
Move wiring into a clear composition/bootstrap layer.

#### Scope
- provider factory wiring
- repository wiring
- storage backend wiring
- execution engine wiring
- service wiring

#### Acceptance criteria
- composition is explicit
- `api/dependencies.py` no longer acts as a hidden composition root bottleneck

---

### Issue L2 — Unify orchestration layers and remove transitional surfaces

#### Goal
Consolidate execution and orchestration wiring after F–K are real.

#### Acceptance criteria
- duplicate/transitional orchestration paths are removed or isolated
- the official runtime flow is clear

---

### Issue L3 — Deployment hardening for offline intranet + remote Postgres + remote storage

#### Goal
Harden the system for the approved deployment model.

#### Scope
- config cleanup
- secrets handling
- remote Postgres safety
- remote storage safety
- health checks / readiness
- operational docs
- remote-safe deployment profile

#### Acceptance criteria
- approved deployment model is explicitly supported
- config is aligned with offline intranet + GigaChat + Postgres + storage backend architecture

---

## Recommended implementation order

1. F1
2. F2
3. F3
4. F4
5. F5
6. G1
7. G2
8. G3
9. H1
10. H2
11. H3
12. I1
13. I2
14. I3
15. J1
16. J2
17. J3
18. K1
19. K2
20. L1
21. L2
22. L3

---

## Rules for Codex during F–L

For every issue:
- keep patches narrow
- do not drift to adjacent phases
- do not redesign the whole architecture
- preserve modular monolith boundaries
- preserve the approved deployment model
- add/update tests
- state commands run
- state test results
- explicitly state blockers instead of silently skipping missing work

For all format-heavy phases:
- do not accept fake format outputs
- validity must be real, not nominal
