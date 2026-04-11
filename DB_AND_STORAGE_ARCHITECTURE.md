# DB_AND_STORAGE_ARCHITECTURE.md

## Purpose

This document defines the target database and storage architecture for **KW Studio** in the approved deployment model:

- server deployment
- no public internet access
- remote access over local network / VPN / bastion
- **GigaChat** as the only active LLM provider
- **Postgres** as the single metadata truth layer
- binary documents and presentations stored through a storage backend
- the system can generate new documents and presentations from:
  - uploaded files
  - existing stored files
  - existing documents/presentations in the system
  - prompt-only requests

This document also fixes the architectural rules that future implementation must follow.

---

# 1. Core architectural rules

## Rule 1 — Postgres is the single metadata truth layer
Postgres is the source of truth for:
- sessions
- tasks
- artifacts
- documents
- presentations
- versions
- lineage/provenance
- extracted content
- execution runs
- LLM runs
- storage references

The project must not keep a second competing metadata truth layer such as SQLite in production.

## Rule 2 — Storage backend is the truth layer for binary files
Real binary files must live in a storage backend, not primarily inside Postgres:
- `.docx`
- `.pptx`
- `.pdf`
- `.xlsx`
- `.csv`
- images
- previews
- temporary binary artifacts

Postgres stores metadata and references to stored binaries, not the primary binary payload as the main storage strategy.

## Rule 3 — Every generated artifact must be traceable to its sources
Every generated document, presentation, report, or analysis output must be traceable to:
- uploaded source files
- existing stored files
- documents
- presentations
- prompt-only origin when no source file exists

This requires explicit lineage / provenance tables.

## Rule 4 — Generation must support 3 input modes
The system must support all of the following:

### Mode A — Uploaded-file-driven generation
User uploads new files and generates outputs from them.

### Mode B — Stored-source-driven generation
User generates outputs from files/documents/presentations that already exist in the system.

### Mode C — Prompt-only generation
User generates outputs from a natural-language request with no uploaded file.

All three modes are first-class product behavior.

## Rule 5 — Deterministic format engines own format correctness
LLM providers do not own binary correctness.

- DOCX validity must be guaranteed by the DOCX pipeline
- PPTX validity must be guaranteed by the PPTX pipeline
- PDF/report output validity must be guaranteed by the PDF/report pipeline

LLMs may provide:
- semantics
- rewriting
- summarization
- outline generation
- content drafting

But deterministic builders must create the final valid artifact.

## Rule 6 — One active LLM provider per deployment
The codebase may contain multiple providers, but each deployment runs with one active provider.

Approved deployment profile for this architecture:
- `LLM_PROVIDER=gigachat`

Other providers may remain implemented but disabled by default.

## Rule 7 — Remote infrastructure is supported
The application must support:
- Postgres hosted on a separate server
- storage backend hosted locally or remotely
- remote user access over LAN/VPN
- remote administration over SSH/VPN/bastion

This is a supported deployment pattern, not an exception.

---

# 2. High-level storage model

The architecture uses two persistence layers:

## Layer A — Postgres
Stores:
- metadata
- relationships
- lineage
- versions
- extracted content
- task state
- execution traces
- file references

## Layer B — Storage backend
Stores:
- binary source files
- binary generated artifacts
- previews
- temporary files
- derived packaged binaries

---

# 3. Storage backend model

The application must not assume only local filesystem storage.

Use a storage abstraction like:

```python
class StorageBackend(Protocol):
    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str: ...
    def read_bytes(self, *, storage_key: str) -> bytes: ...
    def exists(self, *, storage_key: str) -> bool: ...
    def delete(self, *, storage_key: str) -> None: ...
    def get_size(self, *, storage_key: str) -> int | None: ...
    def make_uri(self, *, storage_key: str) -> str: ...
```

## Required storage backend implementations
- `LocalFilesystemStorage`
- `RemoteObjectStorage` interface
- optionally `MinIOStorage` / `S3CompatibleStorage`

## Storage backend responsibility
The backend stores and retrieves binary files.
It does not define business meaning. Business meaning is stored in Postgres.

---

# 4. Recommended storage key patterns

Use deterministic storage keys.

## Uploaded sources
`uploads/{session_id}/{file_id}/{original_filename}`

## Generated artifacts
`artifacts/{session_id}/{task_id}/{artifact_id}/{filename}`

## Previews
`previews/{file_id}/{preview_kind}/{preview_filename}`

## Temporary execution files
`temp/{execution_run_id}/{filename}`

## Derived package artifacts
`derived/{source_file_id}/{derived_kind}/{filename}`

---

# 5. Database table architecture

## 5.1 `sessions`
Represents a user work session.

### Key fields
- `id` UUID / TEXT PK
- `title`
- `created_by`
- `status`
- `created_at`
- `updated_at`

## 5.2 `tasks`
Represents a user task request.

### Key fields
- `id`
- `session_id` FK -> `sessions.id`
- `task_type`
- `status`
- `prompt_text`
- `result_data_json`
- `error_message`
- `started_at`
- `completed_at`
- `created_at`

### Example task types
- `docx_generate`
- `docx_rewrite`
- `pdf_summary`
- `pptx_generate`
- `data_analysis`

## 5.3 `stored_files`
Represents any binary or file-like object known to the system.

### Key fields
- `id`
- `session_id` FK -> `sessions.id`
- `task_id` FK -> `tasks.id`, nullable
- `kind`
- `file_type`
- `mime_type`
- `title`
- `original_filename`
- `storage_backend`
- `storage_key`
- `storage_uri`
- `checksum_sha256`
- `size_bytes`
- `is_remote`
- `created_at`
- `updated_at`

### Example `kind`
- `uploaded_source`
- `generated_artifact`
- `derived_representation`
- `preview`
- `temporary`

### Example `file_type`
- `docx`
- `pptx`
- `pdf`
- `txt`
- `md`
- `json`
- `csv`
- `xlsx`
- `png`

## 5.4 `documents`
Logical document entities.

### Key fields
- `id`
- `session_id` FK -> `sessions.id`
- `current_file_id` FK -> `stored_files.id`
- `document_type`
- `title`
- `status`
- `created_at`
- `updated_at`

### Example `document_type`
- `report`
- `proposal`
- `memo`
- `contract_draft`
- `summary`

## 5.5 `document_versions`
Version history of documents.

### Key fields
- `id`
- `document_id` FK -> `documents.id`
- `file_id` FK -> `stored_files.id`
- `version_number`
- `created_from_task_id` FK -> `tasks.id`
- `parent_version_id` FK nullable -> `document_versions.id`
- `change_summary`
- `created_at`

## 5.6 `presentations`
Logical presentation entities.

### Key fields
- `id`
- `session_id` FK -> `sessions.id`
- `current_file_id` FK -> `stored_files.id`
- `presentation_type`
- `title`
- `status`
- `created_at`
- `updated_at`

### Example `presentation_type`
- `management_deck`
- `sales_pitch`
- `strategy_deck`
- `status_update`

## 5.7 `presentation_versions`
Version history of presentations.

### Key fields
- `id`
- `presentation_id` FK -> `presentations.id`
- `file_id` FK -> `stored_files.id`
- `version_number`
- `created_from_task_id` FK -> `tasks.id`
- `parent_version_id` FK nullable -> `presentation_versions.id`
- `change_summary`
- `created_at`

## 5.8 `artifacts`
Product-level outputs of tasks.

### Key fields
- `id`
- `task_id` FK -> `tasks.id`
- `session_id` FK -> `sessions.id`
- `file_id` FK -> `stored_files.id`
- `artifact_type`
- `title`
- `created_at`

### Example `artifact_type`
- `generated_docx`
- `generated_pptx`
- `summary_report`
- `analysis_chart`
- `derived_text`

## 5.9 `artifact_sources`
Lineage / provenance mapping for generated artifacts.

### Key fields
- `id`
- `artifact_id` FK -> `artifacts.id`
- `source_file_id` FK -> `stored_files.id`, nullable
- `source_document_id` FK -> `documents.id`, nullable
- `source_presentation_id` FK -> `presentations.id`, nullable
- `role`
- `created_at`

### Example `role`
- `primary_source`
- `reference_source`
- `template_source`
- `background_material`

## 5.10 `derived_contents`
Extracted or normalized semantic representations of files.

### Key fields
- `id`
- `file_id` FK -> `stored_files.id`
- `content_kind`
- `text_content`
- `structured_json`
- `outline_json`
- `language`
- `created_at`
- `updated_at`

### Example `content_kind`
- `extracted_text`
- `normalized_structure`
- `slide_outline`
- `document_sections`
- `table_data`

## 5.11 `llm_runs`
Tracks GigaChat calls and future provider calls.

### Key fields
- `id`
- `task_id` FK -> `tasks.id`
- `provider`
- `model`
- `purpose`
- `input_ref`
- `output_ref`
- `usage_json`
- `status`
- `created_at`

### Example `purpose`
- `classification`
- `rewrite`
- `summary`
- `outline_generation`
- `slide_content_generation`

## 5.12 `execution_runs`
Tracks Python execution engine runs.

### Key fields
- `id`
- `task_id` FK -> `tasks.id`
- `engine_type`
- `status`
- `stdout_text`
- `stderr_text`
- `result_json`
- `started_at`
- `completed_at`

---

# 6. Relationships between tables

## Core execution relationships
- `sessions` 1 → N `tasks`
- `sessions` 1 → N `stored_files`
- `tasks` 1 → N `artifacts`
- `tasks` 1 → N `llm_runs`
- `tasks` 1 → N `execution_runs`

## File relationships
- `artifacts` N → 1 `stored_files`
- `documents` N → 1 `stored_files` via `current_file_id`
- `presentations` N → 1 `stored_files` via `current_file_id`
- `stored_files` 1 → N `derived_contents`

## Versioning relationships
- `documents` 1 → N `document_versions`
- `presentations` 1 → N `presentation_versions`
- `document_versions` N → 1 `stored_files`
- `presentation_versions` N → 1 `stored_files`

## Lineage relationships
- `artifacts` 1 → N `artifact_sources`
- `artifact_sources` may point to:
  - `stored_files`
  - `documents`
  - `presentations`

---

# 7. Example user flows and how the schema supports them

## Flow A — User uploads a file manually
Yes, this must be supported.

### Steps
1. User uploads a file.
2. System writes bytes to storage backend.
3. System creates row in `stored_files` with `kind = uploaded_source`.
4. System creates `derived_contents` if extraction succeeds.
5. File becomes selectable as a source for future generation tasks.

## Flow B — User generates from prompt only
Yes, this must be supported.

### Steps
1. User submits prompt with no file attached.
2. System creates `task`.
3. System may generate from prompt only, or reuse stored sources if requested.
4. System creates output file in storage backend.
5. System registers it in `stored_files`.
6. System registers product output in `artifacts`.
7. If it becomes a logical document/presentation, system may also create rows in:
   - `documents` + `document_versions`
   - or `presentations` + `presentation_versions`

## Flow C — User generates a new presentation from an existing presentation
Yes, this must be supported.

### Steps
1. User selects an existing presentation.
2. System resolves its current `stored_files` binary.
3. System reads `derived_contents` such as outline or normalized structure.
4. System creates task.
5. System generates new PPTX.
6. System stores the binary via storage backend.
7. System writes:
   - new `stored_files`
   - new `artifacts`
   - new `presentations` / `presentation_versions` if needed
   - provenance in `artifact_sources`

## Flow D — User generates a new document from existing documents/presentations
Yes, this must be supported.

### Steps
1. System identifies or user selects sources.
2. System resolves source rows from:
   - `stored_files`
   - `documents`
   - `presentations`
3. System reads extracted/structured content from `derived_contents`.
4. GigaChat provides semantics:
   - rewrite
   - summarize
   - combine
   - outline
5. Deterministic builder creates valid output format.
6. Output is stored and lineage is recorded.

---

# 8. Remote Postgres and remote storage

## Remote Postgres
This is fully supported and recommended.

The application connects using a DSN like:

```text
postgresql://user:password@db-host:5432/kw_studio
```

### Required considerations
- connection pooling
- timeouts
- reconnect behavior
- secrets handling
- health checks
- migration safety

## Remote storage backend
This is also supported.

### Recommended model
Treat storage as an external service, not as a local assumption.

Possible backends:
- local filesystem
- remote object storage
- MinIO / S3-compatible storage

### Important
The app connects to:
- Postgres as the metadata truth layer
- storage backend as the binary truth layer

This is the preferred model for your deployment.

---

# 9. What should not be done

## Do not make Postgres the primary binary store for all documents
Technically possible with BLOBs / BYTEA, but not recommended as the primary storage model for `.docx`, `.pptx`, `.pdf`.

## Do not store only file paths with no metadata model
That would make:
- provenance
- versioning
- derived content reuse
- source-driven generation
much weaker.

## Do not skip lineage
Without explicit source relationships, the system cannot safely explain where generated outputs came from.

---

# 10. Recommended implementation order in the roadmap

## Phase F — Foundation and storage truth model

### Goals
- cleanup repository hygiene
- make Postgres the single metadata truth layer
- introduce storage backend abstraction
- support local and remote storage backends
- introduce schema for:
  - stored files
  - documents
  - presentations
  - artifacts
  - lineage
  - derived content

### Deliverables
- Postgres-first repositories
- migration baseline for Postgres
- storage backend abstraction
- `stored_files`
- `documents`
- `document_versions`
- `presentations`
- `presentation_versions`
- `artifacts`
- `artifact_sources`
- `derived_contents`

## Phase G — Execution API

### Goals
Create the official end-to-end application flow:
- create task
- execute task
- get updated task
- get artifact

### Additional requirements
- user can attach uploaded files
- user can select existing stored documents/presentations as sources
- prompt-only tasks are supported

### Deliverables
- public task execution path
- source selection path
- artifact retrieval flow

## Phase H — Real Python execution engine

### Goals
- controlled Python execution engine
- execution run tracking
- local temp file handling
- artifact creation from execution results

### Deliverables
- `execution_runs`
- execution lifecycle
- data-analysis-ready runtime foundation

## Phase I — GigaChat semantic integration

### Goals
- GigaChat provider as the only active runtime provider
- semantic rewriting
- semantic summarization
- outline generation
- classification

### Deliverables
- `llm_runs`
- provider abstraction
- GigaChat implementation
- provider-aware orchestration contracts

## Phase J — Real DOCX/PDF artifact pipelines

### Goals
- true `.docx` output
- true or honest PDF/report output
- use existing documents and presentations as sources
- reuse `derived_contents`
- separate semantics from deterministic binary building

### Deliverables
- real document artifact generation
- source-driven document workflows
- source-driven PDF/report workflows

## Phase K — Real PPTX MVP

### Goals
- true `.pptx` output
- outline-first generation
- use existing stored presentations/documents as sources
- provenance-aware deck generation

### Deliverables
- valid PPTX builder
- source-driven presentation workflows
- downloadable PPTX artifacts

## Phase L — Composition cleanup and deployment hardening

### Goals
- clean composition root
- unify transitional orchestration layers
- harden deployment for:
  - remote Postgres
  - remote storage
  - remote intranet usage
  - secrets/config handling

### Deliverables
- final wiring cleanup
- production deployment profile
- infrastructure-safe configuration model

---

# 11. Required configuration model

The project should support settings like:

```text
DEPLOYMENT_MODE=offline_intranet

POSTGRES_DSN=postgresql://user:password@db-host:5432/kw_studio

STORAGE_BACKEND=local
STORAGE_BASE_PATH=/srv/kw_studio/storage

# or
STORAGE_BACKEND=minio
STORAGE_ENDPOINT=http://storage.local:9000
STORAGE_BUCKET=kw-studio
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=

LLM_PROVIDER=gigachat
GIGACHAT_MODEL=GigaChat-2-Pro
GIGACHAT_CLIENT_ID=
GIGACHAT_CLIENT_SECRET=
GIGACHAT_API_BASE_URL=
GIGACHAT_CA_CERT_PATH=
```

Only one active provider should be used in deployment.

---

# 12. Final decision summary

## Fixed architectural decisions
- Postgres is the single metadata truth layer.
- Binary files live in a storage backend.
- User file upload is a first-class feature.
- Prompt-only generation is a first-class feature.
- Source-driven generation from existing documents/presentations is a first-class feature.
- Remote Postgres is supported.
- Remote storage is supported.
- GigaChat is the primary and only active LLM provider for deployment.
- Provenance and versioning are mandatory.
- Deterministic builders must own binary format correctness.

This architecture is valid for the approved deployment model and should be treated as the baseline for future implementation work.
