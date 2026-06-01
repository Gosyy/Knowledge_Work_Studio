# KR Product Reset Roadmap

This document is the durable roadmap for continuing the KW Studio KR phase after the KR-3D continuation checkpoint.
It prevents a narrow interpretation of KR as only documentation cleanup or test renaming.

KR remains a product reset: move Knowledge_Work_Studio from a stage-history repository toward a portable, offline/intranet, artifact-first, provenance-first, operator-gated knowledge-work studio.

## Why this roadmap exists

Older migration notes correctly described documentation and test cleanup, but that was only the first layer of KR.
The broader KR objective is to prepare the repository for product-quality workflow development.

Future KR patches must therefore explain how they support at least one of these product reset goals:

```text
artifact-first outputs
source evidence and provenance
workflow contracts
quality gates
operator diagnostics
path/profile/commit portability
offline/intranet operation
first-class DOCX/PDF/XLSX/Slides/Python/Browser workflows
safe replacement of historical stage assets
```

## Current factual baseline

The accepted remote continuation point before KR-3E work is:

```text
branch: 9_Product_Release_Hardening
accepted checkpoint: KR-3D
status: project-resident full and Docker smoke validation runners exist
KR-3E status: in progress until targeted checks, full runner, Docker smoke, push, and log review pass
```

The old KR-2A / KR-2B recovery instructions are stale for current development.
They remain useful as history, but they are not the active continuation baseline.

## Product reset pillars

### 1. Artifact-first work products

KW Studio should produce downloadable, inspectable artifacts rather than only chat answers.
Every mature workflow should emit an artifact bundle with manifests, quality reports, and enough metadata to audit what happened.

Expected product direction:

```text
source files + user intent
-> workflow plan
-> controlled deterministic tools
-> generated artifacts
-> validation / render / QA
-> provenance / citations / evidence
-> downloadable outputs
-> task and artifact history
```

### 2. Provenance-first evidence model

Generated output should be traceable back to source material.
Future work should strengthen:

```text
source_evidence_manifest.json
citation_manifest.json
artifact_manifest.json
quality_report.json
review_packet.json
```

Slides, reports, tables, and charts should not make unsupported claims.
Charts and tables should trace back to workbook ranges or explicit source data.

### 3. Operator-gated quality

Operators must be able to understand what happened, rerun checks, inspect logs, and recover from failures.
Every successful patch closure requires:

```text
targeted checks pass
commit
push
full runner pass on committed HEAD
Docker smoke pass on the same committed HEAD
logs archived under the project logs directory
logs reviewed for failures and obvious secret exposure
working tree clean or generated files explicitly restored/acknowledged
```

Full and Docker smoke entrypoints must be project-resident and committed.
External scripts from a downloads directory are allowed only as bootstrap or emergency helpers.

### 4. Offline/intranet operation

Production must not assume public Internet access.
The default production LLM topology remains direct local GigaChat on Server 3.
LiteLLM may be an optional gateway, not a replacement for GigaChat.
Local-small-LLM endpoints are outside active product/runtime scope unless a future ADR explicitly reopens that decision.

Do not claim local_intranet proof, Kimi-level quality, selected parity, or human approval without corresponding evidence artifacts and logs.

### 5. First-class workflow coverage

The mandatory product pillars are:

```text
DOCX workflow
PDF workflow
XLSX / Excel workflow
Slides workflow
Python analysis workflow
Browser-assisted evidence workflow
```

XLSX / Excel is mandatory, not optional.
Slides remain high priority, but they are one pillar of the product, not the whole product.

### 6. Workflow contracts before large feature growth

Before broad feature expansion, KR should converge on shared workflow contracts:

```text
WorkflowInput
WorkflowPlan
WorkflowRun
WorkflowArtifact
WorkflowManifest
WorkflowQualityReport
WorkflowProvenance
```

These contracts should support deterministic tools, local/intranet LLM assistance, validation, artifact history, retry, restore, and audit.

### 7. Safe cleanup of historical stage assets

Historical docs, tests, and scripts are cleanup candidates, but they must not be deleted blindly.
The safe sequence is:

```text
inventory
policy map
replacement coverage
active gate retirement
controlled archive/delete batch
full runner
Docker smoke
```

`docs/codex` remains deprecated development history.
Do not move or delete it until direct checker/test dependencies are cleared.

## Roadmap from the current checkpoint

### KR-3E — Active gate retirement for legacy baseline-pinned scripts

Purpose:

```text
remove active production-readiness-gate dependence on legacy stage baseline-pinned scripts;
keep legacy files available as history or safety-net material;
update legacy smoke expectations to the new product-gate contract;
do not weaken product quality gates.
```

Acceptance:

```text
active gate retirement checker reports ready;
legacy baseline retirement checker remains ready;
path portability checks remain ready;
backend smoke tests pass;
full runner passes from project-resident script;
Docker smoke passes from project-resident script;
logs are archived and reviewed.
```

### KR-3F — Controlled archive/delete batch

Purpose:

```text
archive or delete only inactive legacy docs/checkers that no active product gate, test, or script references;
record every path moved or removed;
keep restore/audit information available.
```

Batch 1 starts with root-level historical prompt packs and old runbooks that are not active product entrypoints.
The archive manifest and machine-checkable guardrail live in:

```text
docs/refactor/CONTROLLED_ARCHIVE_DELETE_READINESS.md
scripts/kw_controlled_archive_delete_readiness_check.py
docs/archive/development-history/root-prompt-packs/
```

Non-goal:

```text
Do not mass-delete docs/codex or legacy tests while direct dependencies remain.
```

### KR-4A — Workflow contract core

Purpose:

```text
introduce shared workflow contract types for all product workflows;
unify plan, manifest, quality, provenance, artifact, and failure reporting concepts;
make future DOCX/PDF/XLSX/Slides/Python/Browser workflows consistent.
```

KR-4A adds the first product-facing contract core rather than rewriting all runtime workflows at once.
The contract core lives in:

```text
backend/app/workflows/core_contracts.py
scripts/kw_workflow_contract_core_check.py
docs/architecture/WORKFLOW_CONTRACT_CORE.md
```

It defines and validates the shared vocabulary future workflows must converge on:

```text
WorkflowInput
WorkflowPlan
WorkflowRun
WorkflowArtifact
WorkflowManifest
WorkflowQualityReport
WorkflowProvenance
```

Mandatory product workflow IDs for the core are:

```text
docx
pdf
xlsx
slides
python_analysis
browser_evidence
```

Non-goal for KR-4A:

```text
do not rewrite every runtime service yet;
do not remove the older S2 workflow registry until compatibility and replacement coverage are proven;
do not collapse Python analysis into XLSX, because both are distinct product pillars.
```

### KR-5A — XLSX inspect workflow

Purpose:

```text
implement the first concrete XLSX inspect workflow;
extract workbook sheets, dimensions, table/range previews, formulas, and basic workbook metadata;
produce an artifact bundle with quality and provenance reports.
```

### KR-5B — XLSX validation and artifact bundle

Purpose:

```text
validate workbook readability;
inventory formulas;
prevent silent destructive edits;
trace charts/tables back to workbook ranges;
package manifests and quality reports.
```

### KR-6A — Source-grounded Slides continuation

Purpose:

```text
continue slides work beyond render infrastructure;
map major claims to source evidence;
prevent unsupported recommendations;
measure citation coverage;
keep independent render QA and artifact bundle checks.
```

### Later product hardening

Future phases may add deeper runtime work after KR-4/KR-5/KR-6 foundations are stable:

```text
persistent workspace history and restore hardening
browser evidence capture contracts
operator diagnostics bundles
local GigaChat intranet proof with evidence
artifact preview, retry, and recovery loops
```


## Migration handoff requirement

KR is now treated as a continuously portable project state, not only a sequence of isolated patches.
The durable migration anchor is:

```text
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
```

Future patches must review and update that handoff document whenever they change project status, accepted checkpoints, workflow direction, validation rules, operating profiles, system dependencies, or the agreed new phase plan.
This is especially required immediately after the user and assistant agree on the plan for a new phase.

The handoff guardrail is:

```text
scripts/kw_project_migration_handoff_check.py
```

The goal is that the project can be moved into another chat, another account, or another assistant with enough context to continue safely.


## Rules for all future patches

Every future patch should state:

```text
what product reset goal it supports;
what problem it solves;
why it is needed now;
what it changes;
what it intentionally does not change;
what targeted checks were run;
what remains out of scope;
what must pass before ACCEPT.
```

Do not:

```text
add product docs under docs/codex;
make active product tests depend on raw historical commit SHAs;
hardcode operator machine paths in product code/tests/docs;
move docs/codex before dependencies are retired;
run npm audit fix --force without a controlled dependency/security patch;
claim offline/GigaChat/Kimi parity without evidence.
```

Profile-specific paths may appear only in local bootstrap scripts or operator instructions for that profile, not in portable project logic.


## KR-5A implementation note

KR-5A adds the first concrete XLSX inspect runtime. Future KR-5B work should build validation and artifact-bundle hardening on this runtime rather than reintroducing ad-hoc spreadsheet checks.

## KR-5B implementation note

KR-5B hardens the XLSX inspect workflow artifact bundle. The accepted direction is:

```text
validate manifest completeness;
validate size and sha256 entries;
use explicit artifact_manifest.json self_reference semantics;
validate formula traceability;
validate source evidence to table previews;
validate quality_report.json fail-closed behavior;
keep the workflow inspect-only and non-destructive.
```

The machine-checkable guardrail is:

```text
scripts/kw_xlsx_validation_bundle_check.py
```

## KR-6A implementation note

KR-6A adds source-grounded Slides continuation on top of the existing Slides source grounding runtime. Acceptance requires:

```text
backend/app/services/slides_service/source_grounded_continuation.py
scripts/kw_slides_source_grounded_continuation_check.py
backend/tests/workflows/test_slides_source_grounded_continuation.py
backend/tests/quality/test_slides_source_grounding_quality.py
backend/tests/smoke/test_slides_source_grounded_continuation_smoke.py
```

The phase is accepted only when citation coverage, source evidence manifest, artifact manifest, quality report, production readiness gate, full runner, Docker smoke, log review, commit, push, and remote verification pass.

### KR-6B — Slides render/visual QA bundle hardening

Purpose:

```text
connect the KR-6A source-grounded Slides bundle to deterministic render artifacts, independent render artifacts, geometry metadata, visual QA report, and fail-closed artifact manifest validation.
```

Acceptance:

```text
scripts/kw_slides_render_visual_qa_bundle_check.py reports ready;
render_manifest.json covers primary and independent render artifacts;
geometry_report.json covers every slide;
visual_qa_report.json is ready and fail-closed;
artifact_manifest.json lists render, geometry, visual QA, citation, and source evidence artifacts;
full runner and Docker smoke pass from project-resident scripts.
```

Non-goals:

```text
no claim of broad presentation feature coverage;
no replacement for later real PPTX render integration and deeper visual comparison.
```


## KR-GOV-1 — Assistant Decision Governance

Purpose:

```text
consolidate assistant operating rules, Definition of Done, prohibitions, quality matrix, report templates, ADR policy, and machine-checkable governance validation;
make it harder for future assistants to forget rules, simplify tasks, issue unverified patches, or hide product failures behind workarounds;
keep documentation maintainable as the project continues through KR-7 and later phases.
```

Implementation surface:

```text
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/adr/0001-assistant-decision-governance.md
docs/templates/PRE_PATCH_REPORT_TEMPLATE.md
docs/templates/POST_PATCH_REPORT_TEMPLATE.md
docs/templates/LOG_ANALYSIS_TEMPLATE.md
scripts/kw_assistant_governance_check.py
```

Documentation stewardship is part of KR-GOV-1. Future assistants must update the closest authoritative document first and use `PROJECT_MIGRATION_HANDOFF.md` for durable summaries and links, not as an unstructured dumping ground.

Acceptance:

```text
scripts/kw_assistant_governance_check.py --repo-root . --require-ready passes;
assistant governance check is included in the project full runner;
AGENTS.md, README.md, CODEX_PROJECT_BRIEFING.md, and PROJECT_MIGRATION_HANDOFF.md reference the governance layer;
git diff --check passes;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7B.2 fake/noop provider test-double boundary

Purpose:

```text
finish the second layer of KR-7B active provider cleanup by ensuring fake/noop LLM providers are explicit app_env=test doubles only;
reject fake/noop in development, production, offline/intranet runtime, and operator workflows;
keep GigaChat as the only active runtime provider while preserving test doubles for isolated tests.
```

Acceptance:

```text
provider factory rejects fake/noop outside app_env=test;
composition only wires fake/noop LLM text service under app_env=test;
LLM provider scope checker passes;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7B.3 final provider-scope UI/docs/config claim audit

Purpose:

```text
finish KR-7B by auditing remaining UI, docs, config examples, schema drafts, and fixtures for provider-scope claims;
ensure active project surfaces do not present legacy local-model, arbitrary local LLM, fake provider, or noop provider options as runtime/development/product choices;
make scripts/kw_llm_provider_scope_check.py verify residual claim boundaries.
```

Acceptance:

```text
production-like examples omit fake/noop runtime settings;
product docs say GigaChat intranet first rather than generic local LLM first;
CODEX briefing says fake/noop are app_env=test doubles only;
SQL_DRAFT_SCHEMA_V1.sql does not whitelist obsolete openai/qwen/noop provider values;
active test fixtures avoid presenting legacy local-model fallback as a current option;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7C.1 API-first Presentation contract skeleton

Purpose:

```text
start KR-7C by exposing a versioned /api/v1 Presentation contract that can be consumed by replaceable frontend clients;
keep legacy /tasks and unversioned presentation endpoints as compatibility adapters;
fail closed for future mutation/render/export/quality endpoints until their runtime implementation is delivered in later KR-7C subphases.
```

Acceptance:

```text
/api/v1/presentations OpenAPI contract exists;
/api/v1/presentations/{presentation_id} exposes safe metadata;
/api/v1/presentations/{presentation_id}/plan and /slides expose safe plan/slide payloads from existing snapshots;
future mutation/render/export/quality endpoints return explicit 501 instead of pretending to work;
scripts/kw_presentation_api_contract_check.py passes;
legacy /tasks slides path remains available;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7C.2 PresentationIR versioning and persistence contract

Purpose:

```text
add the first stable `presentation_ir.v1` envelope and validation helpers;
allow existing legacy plan snapshots to be exposed as PresentationIR-compatible API payloads without pretending a new planner exists;
allow native PresentationIR payloads to be validated and persisted through the plan snapshot store;
expose read-only PresentationIR version metadata through API-first endpoints.
```

Acceptance:

```text
PresentationIR payloads require explicit schema_version, deck, theme, sources, assets, slides, and quality_contract fields;
legacy plan snapshots are adapted to `presentation_ir.v1` for API reads;
native PresentationIR snapshots are validated before persistence;
/api/v1/presentations/{presentation_id}/ir exposes the latest safe PresentationIR payload;
/api/v1/presentations/{presentation_id}/ir/versions lists persisted IR-compatible snapshot versions;
scripts/kw_presentation_api_contract_check.py verifies the new paths, schemas, and source helpers;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7C.3 Presentation source attachment/read contract

Purpose:

```text
complete the next API-first Presentation contract layer by exposing source attachment metadata through /api/v1 without implementing KR-7D extraction runtime;
make PresentationIR source references canonical, validated, versioned, and safe to read from API clients;
keep source attachment mutation fail-closed until persistence/mutation behavior is implemented in a later subphase.
```

Acceptance:

```text
PresentationIR sources require source_id, source_type, role, and extraction_status;
/api/v1/presentations/{presentation_id}/sources returns safe source metadata from the latest PresentationIR-compatible snapshot;
legacy snapshots return an empty source list without claiming extraction;
source attachment POST remains explicit 501 until mutation/runtime persistence exists;
scripts/kw_presentation_api_contract_check.py verifies the source read path, schemas, and source helper phrases;
full runner and Docker smoke pass before LOCAL ACCEPT.
```


### KR-7D.1 Offline source ingestion engine foundation

Purpose:

```text
start KR-7D by adding a deterministic offline source ingestion engine foundation for Presentation workflows;
extract local source structure without public internet, LLMs, OCR, generated images, or hidden embedding services;
produce provenance-first fragments, structured table candidates, and source asset registry reports that later KR-7E/F/J/K phases can consume.
```

Acceptance:

```text
backend/app/services/slides_service/offline_source_ingestion.py defines offline_source_ingestion.v1 and source_asset_registry.v1 contracts;
DOCX, PPTX, XLSX/CSV, Markdown/text ingestion produces fragments/tables/assets with provenance references;
PDF extraction remains honest and dependency-gated: PyMuPDF/fitz may extract text when available, otherwise the report is unsupported rather than fake success;
unsupported formats return unsupported reports instead of fallback text;
scripts/kw_offline_source_ingestion_check.py verifies the runtime/checker/docs surface and is included in the full runner;
test inventory classifies the KR-7D checker;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement KR-7E evidence retrieval, embeddings, OCR, source-to-slide planning, render/export, quality scoring, or UI source management in KR-7D.1;
do not claim complete PDF/OCR readiness unless dependency-backed extraction proves it in logs.
```


### KR-7D.2 SourceAssetRegistry persistence and extracted asset storage contract

Purpose:

```text
turn KR-7D.1 extracted source asset metadata into a deterministic persistence contract;
store extracted image/media bytes under a profile-neutral SourceAssetRegistry storage root;
write source_asset_storage.v1 manifests with relative paths, source-asset URIs, checksums, sizes, provenance refs, and sanitized source package paths;
keep the storage layer independent from KR-7E evidence retrieval, KR-7F PresentationIR planning, render/export, OCR, and UI source management.
```

Acceptance:

```text
backend/app/services/slides_service/source_asset_registry.py defines source_asset_storage.v1 and SourceAssetRegistryStore;
extracted asset bytes from DOCX/PPTX/XLSX packages can be persisted with checksum verification;
public registry manifests expose relative paths and source-asset:// URIs, not operator absolute paths;
ingestion report JSON written by the store is safe to serialize and does not contain raw content_bytes;
empty asset reports are persisted as honest empty manifests, not fake success;
scripts/kw_offline_source_ingestion_check.py verifies the storage/checker/docs surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement KR-7E evidence retrieval, OCR, embeddings, source-to-slide planning, render/export, quality scoring, or UI source management in KR-7D.2;
do not claim complete SourceAssetRegistry product integration beyond the storage contract and manifest persistence layer.
```


### KR-7D.3 Richer document structure extraction

Purpose:

```text
deepen the KR-7D offline ingestion engine beyond first-pass text/table/media extraction;
emit source_structure.v1 structure elements and chart candidates for DOCX/PPTX/XLSX/PDF/Markdown;
make later KR-7E evidence retrieval and KR-7F planning consume richer provenance-ready structure without implementing those later phases now.
```

Acceptance:

```text
backend/app/services/slides_service/offline_source_ingestion.py exposes SourceStructureElement, SourceChartDataCandidate, and SOURCE_STRUCTURE_SCHEMA_VERSION;
Markdown ingestion reports headings, code blocks, image refs, and tables as structure elements;
DOCX ingestion reports paragraph styles, captions, tables, and inline images as structure elements;
PPTX ingestion reports slides, text boxes, tables, and chart data candidates;
XLSX ingestion reports worksheet/formula structure and chart data candidates;
PDF ingestion reports page/text block coordinate structure when PyMuPDF/fitz is available and remains honest unsupported otherwise;
scripts/kw_offline_source_ingestion_check.py verifies the richer structure/checker/docs surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement KR-7E evidence retrieval, OCR, embeddings, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management in KR-7D.3;
do not claim source_structure.v1 elements are evidence relevance rankings or user-visible source-backed slide planning.
```

### KR-7D.4 Real package extraction fidelity and dependency-backed extractors

Purpose:

```text
harden KR-7D extraction against real DOCX/PPTX/XLSX/PDF package structure;
record source_extraction_fidelity.v1 metadata for every ingestion report;
resolve OOXML relationships so embedded media and chart/package references remain traceable to their owner parts;
record optional dependency status for dependency-backed extractors without requiring public internet or hidden services.
```

Acceptance:

```text
backend/app/services/slides_service/offline_source_ingestion.py exposes SOURCE_EXTRACTION_FIDELITY_SCHEMA_VERSION and extraction_fidelity report metadata;
DOCX media assets preserve relationship id, owner part, relationship target/type, checksum, provenance ref, and optional image dimensions;
PPTX media assets preserve slide number, owner part, relationship id, relationship target/type, checksum, provenance ref, and optional image dimensions;
XLSX/PPTX/DOCX reports include package required-part and relationship-count metadata;
PDF reports include PyMuPDF/fitz dependency status and remain unsupported/failed honestly when runtime extraction cannot prove content;
scripts/kw_offline_source_ingestion_check.py verifies the fidelity/checker/docs surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement KR-7E evidence retrieval, OCR, embeddings, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management in KR-7D.4;
do not claim complete dependency-backed extraction unless dependency status metadata and logs prove it.
```


### KR-7E.1 Offline evidence index foundation

Purpose:

```text
start KR-7E by replacing web research assumptions with a deterministic local evidence index;
build offline_evidence_index.v1 from KR-7D ingestion reports;
index source fragments, tables, structure elements, and chart candidates with provenance refs;
provide lexical_token_index, BM25-like IDF scoring, and source section scoring with no hidden embedding dependency;
fail closed for unsupported claims and prompt-only decks with no local sources.
```

Acceptance:

```text
backend/app/services/slides_service/offline_evidence_index.py defines offline_evidence_index.v1 and OfflineEvidenceIndexBuilder;
search results return evidence ids, source ids, provenance refs, matched terms, scores, and location metadata;
claim assessment reports supported/unsupported status without pretending prompt-only decks are research-backed;
scripts/kw_offline_evidence_index_check.py verifies the evidence-index/checker/docs surface;
scripts/kw_full_tests_with_proxy_runner.sh runs the KR-7E checker before the production readiness gate;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management in KR-7E.1;
do not claim complete evidence retrieval quality beyond the deterministic lexical foundation and unsupported-claim guardrails.
```

### KR-7E.2 evidence-to-source-section scoring and unsupported-claim reporting hardening

Purpose:

```text
harden the KR-7E offline evidence index so claim support is evaluated against source sections, not only individual lexical fragments;
add section-level scores, claim-term coverage ratios, missing-term reporting, and structured unsupported-claim reports;
keep the implementation deterministic and local-source-only, without embeddings, web research, PostgreSQL FTS runtime claims, planner integration, render/export, or UI work.
```

Acceptance:

```text
OfflineEvidenceIndex exposes search_sections(query) and section_index metadata;
EvidenceSearchResult includes coverage_ratio, section_id, section_label, and section_score;
ClaimEvidenceAssessment includes offline_unsupported_claim_report.v1 when a claim is unsupported;
unsupported reports list claim_terms, matched_terms, missing_terms, top_candidate_sections, unsupported_sources, and required_action;
scripts/kw_offline_evidence_index_check.py verifies the KR-7E.2 surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management in KR-7E.2;
do not claim a supported result when required claim terms are missing from local evidence sections.
```

### KR-7E.3 evidence index persistence and retrieval API read contract

Purpose:

```text
persist deterministic offline evidence indexes so API clients can read evidence metadata, search results, and claim assessments without coupling to a specific UI;
expose read-only /api/v1 Presentation evidence endpoints while keeping generation/planning/rendering out of scope;
keep persisted manifests public-safe with relative paths, checksums, source evidence schema versions, and no operator absolute storage paths.
```

Acceptance:

```text
backend/app/services/slides_service/offline_evidence_index.py defines offline_evidence_index_storage.v1 and OfflineEvidenceIndexStore;
GET /api/v1/presentations/{presentation_id}/evidence reads persisted index metadata;
GET /api/v1/presentations/{presentation_id}/evidence/search searches persisted local evidence;
GET /api/v1/presentations/{presentation_id}/evidence/claims returns persisted-index claim assessments and structured unsupported reports;
scripts/kw_offline_evidence_index_check.py and scripts/kw_presentation_api_contract_check.py verify the KR-7E.3 surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management in KR-7E.3;
do not expose operator absolute paths or treat evidence persistence as planner/render runtime.
```

### KR-7F.1 PresentationIR planner foundation

Purpose:

```text
start KR-7F by adding a deterministic PresentationIR planner foundation;
consume KR-7E offline evidence index results to build validated presentation_ir.v1 drafts;
represent deck strategy, slide roles, takeaways, blocks, visual plans, and evidence bindings without inventing evidence;
fail closed when source evidence is required but missing, and mark prompt-only output as explicitly degraded.
```

Acceptance:

```text
backend/app/services/slides_service/presentation_ir_planner.py defines presentation_ir_planner.v1 and PresentationIRPlannerFoundation;
planner output validates through require_presentation_ir_payload;
every ready/degraded slide has role, takeaway, blocks, and visual_plan;
evidence-bound slides preserve evidence_id, source_id, provenance_ref, section metadata, score, and matched terms;
charts require real numeric data and are not emitted by KR-7F.1 unless supported later by data-binding phases;
images are not required or generated by KR-7F.1;
fallback is degraded and explicit;
missing required evidence returns blocked, not invented evidence;
scripts/kw_presentation_ir_planner_check.py verifies the KR-7F.1 surface and is included in the full runner;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement final GigaChat PresentationIR planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime in KR-7F.1;
do not claim final GigaChat planning runtime from KR-7F.1;
do not claim prompt-only degraded planner drafts are source-backed.
```

### KR-7F.2 evidence-aware slide outline planning hardening

Purpose:

```text
harden KR-7F planner foundation so it plans slide outlines against local evidence sections before building PresentationIR slides;
introduce presentation_ir_outline.v1 records with slide role, title, intent query, expected terms, support status, coverage ratio, evidence bindings, missing terms, and warnings;
make degraded/unsupported slide outlines explicit without pretending they are source-backed or final GigaChat planning runtime.
```

Acceptance:

```text
backend/app/services/slides_service/presentation_ir_planner.py defines PRESENTATION_IR_OUTLINE_SCHEMA_VERSION and PresentationIRSlideOutline;
PresentationIRPlannerResult includes slide_outlines and coverage_summary;
PresentationIR slides include outline metadata and quality_contract records evidence_aware_outline_planning, outline_coverage_ratio, supported/unsupported slide counts;
custom required_sections influence non-cover/non-closing slide roles without hardcoding source-free claims;
low outline coverage returns degraded with outline_coverage_below_required_threshold instead of ready;
prompt-only outlines mark every slide unsupported and remain degraded;
scripts/kw_presentation_ir_planner_check.py verifies the KR-7F.2 surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement final GigaChat PresentationIR planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime in KR-7F.2;
do not claim evidence-aware slide outline planning is final GigaChat planning runtime;
do not claim unsupported slide outlines are source-backed.
```

### KR-7F.3 planner persistence and PresentationIR snapshot API contract hardening

Purpose:

```text
harden persistence of deterministic planner output as PresentationIR snapshots;
attach presentation_ir_planner_snapshot.v1 metadata to persisted PresentationIR payloads;
expose planner snapshot metadata through existing read-only PresentationIR snapshot API responses and version summaries;
fail closed when a blocked planner result is asked to become a persisted PresentationIR snapshot.
```

Acceptance:

```text
backend/app/services/slides_service/presentation_ir_planner.py defines presentation_ir_planner_snapshot.v1 and persistable planner-result helpers;
PresentationPlanSnapshotService can create planner-backed PresentationIR snapshots only when planner output is persistable;
GET /api/v1/presentations/{presentation_id}/ir includes public-safe planner_snapshot metadata when present;
GET /api/v1/presentations/{presentation_id}/ir/versions includes planner_snapshot metadata in version summaries;
scripts/kw_presentation_ir_planner_check.py and scripts/kw_presentation_api_contract_check.py verify the KR-7F.3 surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement final GigaChat PresentationIR planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime in KR-7F.3;
do not persist blocked planner results as successful PresentationIR snapshots.
```

### KR-7G.1 visual grammar library foundation

Purpose:

```text
start KR-7G by defining the first professional editable visual grammar library;
introduce presentation_visual_grammar.v1 block specs and validators for executive summary cards, KPI cards, process flow, roadmap, timeline, 2x2 matrix, SWOT, comparison table, decision matrix, risk matrix, architecture diagram, funnel, data table, and native chart from real data;
enforce semantic purpose, source refs, diagram nodes/items, and native chart real numeric source data refs without claiming renderer output.
```

Acceptance:

```text
backend/app/services/slides_service/visual_grammar.py defines presentation_visual_grammar.v1, PresentationVisualGrammarLibrary, VisualGrammarBlockSpec, and VisualGrammarValidationResult;
every block has semantic purpose and validator;
every catalog block has semantic purpose and a validator;
native chart blocks require real numeric data and source data refs;
native chart blocks require real numeric series plus source_ref/data_ref and fail closed without them;
diagram-like blocks require nodes, edges, steps, phases, stages, or items;
scripts/kw_visual_grammar_check.py verifies the KR-7G.1 surface and is included in the full runner;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, quality scoring, or UI runtime in KR-7G.1;
do not claim visual grammar validators prove renderer output quality;
do not accept native_chart visual grammar blocks without real numeric source data and source data refs.
```

### KR-7G.2 bind visual grammar blocks into PresentationIR planner output

Purpose:

```text
bind presentation_visual_grammar.v1 block contracts into deterministic PresentationIR planner output;
ensure source-backed slide outlines produce editable visual grammar blocks with validation metadata;
keep unsupported or prompt-only outlines explicit and blocked instead of pretending visual blocks are source-backed.
```

Acceptance:

```text
backend/app/services/slides_service/presentation_ir_planner.py defines presentation_ir_visual_grammar_binding.v1;
PresentationIR slides include visual grammar block metadata when source evidence bindings exist;
quality_contract records visual grammar schema, binding schema, bound block count, blocked block count, and binding status;
prompt-only/degraded planner output does not bind source-backed visual grammar blocks;
data-oriented planner roles use source-backed data_table blocks rather than fake native_chart blocks;
scripts/kw_presentation_ir_planner_check.py and scripts/kw_visual_grammar_check.py verify the KR-7G.2 surface;
full runner and Docker smoke pass before LOCAL ACCEPT.
```

Non-goals:

```text
do not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, quality scoring, or UI runtime in KR-7G.2;
do not claim visual grammar blocks are source-backed when planner output has no evidence bindings.
```

### KR-7G.3 visual grammar API/catalog/read contract hardening

Purpose:

```text
expose presentation_visual_grammar.v1 through read-only API v1 surfaces;
make the catalog and PresentationIR visual grammar bindings visible to clients without implying renderer runtime;
validate read-side bindings with PresentationVisualGrammarLibrary before returning status metadata.
```

Acceptance:

```text
GET /api/v1/presentation-visual-grammar/catalog returns the catalog, block specs, non-goals, and renderer_runtime_implemented=false;
GET /api/v1/presentations/{presentation_id}/visual-grammar reads the latest public-safe PresentationIR snapshot and returns validated binding status;
legacy snapshots without visual grammar bindings return status=empty instead of pretending runtime output exists;
OpenAPI exposes visual grammar schemas and endpoints;
scripts/kw_visual_grammar_check.py and scripts/kw_presentation_api_contract_check.py verify the API/catalog/read contract surface.
```

Non-goals:

```text
do not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, quality scoring, or UI runtime in KR-7G.3;
do not claim catalog/read APIs render editable visuals or prove PPTX output quality.
```

### KR-7H.1 renderer worker boundary contract preflight

Purpose:

```text
establish the fail-closed renderer boundary contract for Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle;
validate renderer-worker input readiness without starting a Node worker, creating a PPTX, running LibreOffice, or claiming production-quality output;
make renderer_runtime_implemented=false explicit until later KR-7H runtime patches implement real rendering and proof generation.
```

Acceptance:

```text
backend/app/services/slides_service/renderer_worker_contract.py defines presentation_renderer_worker_contract.v1 and presentation_renderer_worker_input.v1;
renderer_worker_boundary_contract_payload() declares the future Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle boundary;
validate_renderer_worker_input_payload() fails closed for invalid PresentationIR, blocked visual grammar bindings, fake native chart data, non-source assets, and renderer/runtime output claims;
build_renderer_worker_input_payload() returns contract-only JSON with renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false;
scripts/kw_renderer_worker_contract_check.py verifies the KR-7H.1 boundary surface and is included in the full runner.
```

Non-goals:

```text
do not implement production PPTX rendering in KR-7H.1;
do not start a Node/PptxGenJS worker, run LibreOffice, generate PDF/PNG proof artifacts, add UI runtime, add quality scoring, or claim rendered output quality;
do not treat artifact/proof bundle declarations as produced artifacts.
```

### KR-7H.2 renderer worker dry-run scaffold contract

Purpose:

```text
add a deterministic Python-side dry-run scaffold on top of the KR-7H.1 renderer boundary;
turn validated PresentationIR into renderer-worker input and a renderer-worker dry-run report;
emit presentation_renderer_worker_dry_run.v1 and presentation_renderer_worker_invocation_manifest.v1 without starting Node/PptxGenJS, creating PPTX, running LibreOffice, or claiming production-quality output.
```

Acceptance:

```text
backend/app/services/slides_service/renderer_worker_dry_run.py defines presentation_renderer_worker_dry_run.v1 and presentation_renderer_worker_invocation_manifest.v1;
build_renderer_worker_dry_run_report() validates PresentationIR through KR-7H.1 renderer input validation and returns ready only for source-backed, fail-closed renderer input;
blocked PresentationIR, prompt-only visual grammar gaps, fake native_chart data, runtime claims, and artifact/proof production claims remain blocked;
ready dry-run reports include an invocation manifest describing the future Node/PptxGenJS worker input but keeping renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false;
scripts/kw_renderer_worker_dry_run_check.py verifies the dry-run scaffold and is included in the full runner.
```

Non-goals:

```text
do not generate production PPTX in KR-7H.2;
do not start Node/PptxGenJS;
do not run LibreOffice;
do not add a PptxGenJS dependency, generate PDF/PNG proof artifacts, add UI runtime, add visual QA, add quality scoring, or claim rendered output quality;
do not treat the dry-run invocation manifest as a produced artifact/proof bundle.
```

KR-7H.2 guardrail summary:

```text
KR-7H.2 does not generate production PPTX.
KR-7H.2 does not start Node/PptxGenJS.
KR-7H.2 does not run LibreOffice.
```

### KR-7H.3 renderer worker protocol preflight scaffold

Purpose:

```text
add a deterministic Node-side protocol preflight scaffold after the KR-7H.2 dry-run invocation manifest;
validate presentation_renderer_worker_dry_run.v1 and presentation_renderer_worker_invocation_manifest.v1 at the future worker boundary;
return presentation_renderer_worker_protocol_preflight_response.v1 fail-closed JSON without generating PPTX, importing or executing PptxGenJS, running LibreOffice, or claiming production-quality output.
```

Acceptance:

```text
renderer_worker/kw_renderer_worker_protocol_preflight.mjs defines presentation_renderer_worker_protocol_preflight.v1 and presentation_renderer_worker_protocol_preflight_response.v1;
the protocol preflight accepts only ready dry-run reports with valid renderer input and invocation manifest schemas;
invalid JSON, prompt-only/blocked dry-run reports, runtime claims, and artifact/proof production claims fail closed;
scripts/kw_renderer_worker_protocol_check.py verifies the Node-side protocol preflight and is included in the full runner;
backend/tests/services/test_kr7h_renderer_worker_protocol.py covers capabilities, ready source-backed preflight, blocked prompt-only input, runtime/bundle claim rejection, and invalid JSON.
```

Non-goals:

```text
do not generate PPTX in KR-7H.3;
do not import or execute PptxGenJS;
do not start a production renderer worker service;
do not run LibreOffice;
do not generate PDF/PNG proof artifacts, add UI runtime, add visual QA, add quality scoring, or claim rendered output quality;
do not treat protocol preflight responses as produced artifact/proof bundles.
```

KR-7H.3 guardrail summary:

```text
KR-7H.3 does not generate PPTX.
KR-7H.3 does not import or execute PptxGenJS.
KR-7H.3 does not run LibreOffice.
```

### KR-7H.4 isolated renderer worker package preflight

Purpose:

```text
add an isolated renderer_worker package boundary after the KR-7H.3 Node-side protocol preflight scaffold;
keep renderer worker package scripts separate from frontend UI package scripts and dependencies;
verify presentation_renderer_worker_package_preflight.v1 readiness through deterministic npm scripts without adding PptxGenJS, generating PPTX, running LibreOffice, or claiming production-quality output.
```

Acceptance:

```text
renderer_worker/package.json defines a private kw-studio-renderer-worker package with type=module and no dependencies/devDependencies;
renderer_worker/package.json exposes npm run protocol:preflight and npm run check;
renderer_worker/CONTRACT.md documents package isolation, required scripts, runtime flags, and non-goals;
scripts/kw_renderer_worker_package_check.py validates package.json, package scripts, frontend package isolation, and protocol capabilities;
backend/tests/services/test_kr7h_renderer_worker_package.py covers package metadata, npm scripts, contract text, and frontend isolation;
scripts/kw_full_tests_with_proxy_runner.sh includes the 29h4-renderer-worker-package-check step.
```

Non-goals:

```text
do not generate PPTX in KR-7H.4;
do not add PptxGenJS dependency;
do not map PresentationIR blocks into slides;
do not start a long-running renderer worker service;
do not run LibreOffice;
do not produce PDF/PNG proof artifacts or artifact/proof bundles;
do not perform visual QA or quality scoring;
do not change frontend package.json for renderer worker needs;
do not change UI, GigaChat runtime, embeddings, web research, or dependency/security policy.
```

KR-7H.4 guardrail summary:

```text
KR-7H.4 does not generate PPTX.
KR-7H.4 does not add PptxGenJS dependency.
KR-7H.4 does not run LibreOffice.
KR-7H.4 package preflight responses are not rendered deck artifacts.
```

### KR-7H.5 controlled PptxGenJS capability preflight

KR-7H.5 introduces a controlled PptxGenJS capability preflight after the isolated renderer worker package boundary.

Scope:

- declare `pptxgenjs@4.0.1` only inside `renderer_worker/package.json`;
- commit `renderer_worker/package-lock.json` for the isolated worker package;
- add `presentation_renderer_worker_pptxgenjs_capability.v1` capability output;
- validate dependency availability/version through deterministic npm and Node checks;
- keep frontend package/dependency policy unchanged;
- add project-resident checker, service tests, and full-runner coverage.

Non-goals:

- does not generate PPTX;
- does not map PresentationIR blocks into slides;
- does not call PptxGenJS output/write APIs;
- does not run LibreOffice;
- does not produce artifact/proof bundles;
- does not perform visual QA or quality scoring;
- does not change UI or GigaChat runtime;
- does not run npm audit fix or unrelated dependency cleanup.


### KR-7H.6 in-memory PptxGenJS construction preflight

KR-7H.6 introduces `presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1` after the controlled PptxGenJS capability preflight. It is the first API-level smoke that constructs a PptxGenJS presentation object in memory only.

Scope:

- import pinned `pptxgenjs@4.0.1` from the isolated `renderer_worker` package;
- construct `new PptxGenJS()` in memory and return deterministic JSON;
- verify `slide_count=0`, `slide_content_added=false`, `pptxgenjs_write_api_called=false`, and `filesystem_output_written=false`;
- keep frontend package/dependency policy unchanged;
- add project-resident checker, service tests, and full-runner coverage.

Non-goals:

- does not write .pptx files;
- does not map PresentationIR blocks into slides;
- does not add slide content;
- does not call PptxGenJS write/output APIs;
- does not run LibreOffice;
- does not produce artifact/proof bundles;
- does not perform visual QA or quality scoring;
- does not change UI or GigaChat runtime;
- does not run npm audit fix or unrelated dependency cleanup.


### KR-7H.7 controlled empty PPTX file output smoke

KR-7H.7 introduces `presentation_renderer_worker_empty_pptx_output_smoke.v1` after the in-memory PptxGenJS construction preflight. It is the first controlled writer capability smoke, but it is still not a production renderer.

Scope:

- call PptxGenJS `writeFile` only for a temporary empty `.pptx` inside the isolated `renderer_worker` package;
- verify `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, and `temporary_pptx_file_size_nonzero=true`;
- keep `persistent_artifact_written=false`, `filesystem_output_written=false`, `presentation_ir_mapping_implemented=false`, and `production_pptx_output_implemented=false`;
- keep frontend package/dependency policy unchanged;
- add project-resident checker, service tests, and full-runner coverage.

Non-goals:

- does not create production PPTX output;
- does not map PresentationIR blocks into slides;
- does not add slide content;
- does not persist PPTX artifacts;
- does not run LibreOffice;
- does not produce artifact/proof bundles;
- does not perform visual QA or quality scoring;
- does not change UI or GigaChat runtime;
- does not run npm audit fix or unrelated dependency cleanup.

Validation closure must include targeted apply checks, exact local patch/package testing on the assistant copy, full runner, Docker smoke, clean/classified tree, reviewed logs, then push and remote HEAD verification before REMOTE ACCEPT / CLOSED.


### KR-7H.8 controlled static single-slide PPTX output smoke

KR-7H.8 introduces `presentation_renderer_worker_static_slide_output_smoke.v1` after the controlled empty PPTX file output smoke. It is the first static slide-content writer capability smoke, but it is still not a production renderer.

Scope:

- call PptxGenJS `addSlide` / `addText` only for one fixed technical smoke slide inside the isolated `renderer_worker` package;
- call PptxGenJS `writeFile` only for a temporary `.pptx` in an ephemeral directory;
- verify `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, `temporary_pptx_file_size_nonzero=true`, `static_slide_count=1`, `static_slide_content_added=true`, `static_slide_uses_user_content=false`, and `static_slide_uses_presentation_ir=false`;
- keep `persistent_artifact_written=false`, `filesystem_output_written=false`, `presentation_ir_mapping_implemented=false`, and `production_pptx_output_implemented=false`;
- keep frontend package/dependency policy unchanged;
- add project-resident checker, service tests, and full-runner coverage.

Non-goals:

- does not create production PPTX output;
- does not map PresentationIR blocks into slides;
- does not use user prompt content or source evidence content;
- does not persist PPTX artifacts;
- does not run LibreOffice;
- does not produce artifact/proof bundles;
- does not perform visual QA or quality scoring;
- does not change UI or GigaChat runtime;
- does not run npm audit fix or unrelated dependency cleanup.

Validation closure must include targeted apply checks, exact local patch/package testing on the assistant copy, full runner, Docker smoke, clean/classified tree, reviewed logs, then push and remote HEAD verification before REMOTE ACCEPT / CLOSED.

### KR-7H post-7H.8 consolidation plan

After KR-7H.8 the remaining native renderer-worker phase is intentionally consolidated into larger, still bounded patches:

```text
KR-7H.9  — minimal PresentationIR mapping + single/multi-slide temporary PPTX smoke
KR-7H.10 — persistent PPTX artifact bundle + render report contract
KR-7H.11 — LibreOffice proof bundle smoke
KR-7H.12 — renderer hardening: source-image-only, fail-closed, no fake artifacts
KR-7H.13 — KR-7H closure gate
```

This consolidation is accepted because KR-7H.1 through KR-7H.8 already established the safe renderer-worker boundary, isolated Node package, controlled PptxGenJS dependency, in-memory construction, temporary file output, and static-slide output. Future KR-7H patches may be broader than earlier micro-preflight patches, but only when they remain inside one coherent architectural layer and keep explicit non-goals.

Consolidation guardrails:

- KR-7H.9 may combine minimal PresentationIR mapping with single-slide and multi-slide temporary PPTX smoke, but must not create persistent artifacts or LibreOffice proofs;
- KR-7H.10 may introduce persistent PPTX artifact bundle writing and render report contracts, but must not run LibreOffice proof generation or visual QA;
- KR-7H.11 may introduce LibreOffice proof-bundle smoke, but must not broaden mapping into full professional layout or visual scoring;
- KR-7H.12 may harden source-image-only behavior, fail-closed paths, and no-fake-artifact guarantees, but must not add unrelated UI/GigaChat/runtime/dependency cleanup;
- KR-7H.13 is the closure gate and must verify the whole KR-7H renderer-worker contract with targeted checks, full runner, Docker smoke, clean/classified tree, reviewed logs, push, and remote HEAD verification.

The consolidated KR-7H plan replaces any assumption that future KR-7H work must continue as many tiny preflight patches. It does not relax quality gates: every patch still requires a valid current full-history checkout, exact patch/package testing on the assistant side, self-contained apply runner, targeted apply-log review, committed local full runner, Docker smoke, and remote verification before closure.


Implementation note after KR-7H.9:

KR-7H.9 adds `presentation_renderer_worker_minimal_ir_mapping_smoke.v1` and validates minimal title/body mapping from renderer input into temporary single-slide and multi-slide PPTX smoke outputs. It deletes all temporary outputs and still does not create persistent artifacts, LibreOffice proofs, proof bundles, visual QA, chart/table/image mappings, or production-quality PPTX output.


### KR-7H.9 minimal PresentationIR mapping + single/multi-slide temporary PPTX smoke

KR-7H.9 implements the first controlled renderer mapping smoke. It may map only title/body text from validated renderer input / source-backed dry-run payloads into temporary single-slide and multi-slide PPTX files, verify non-zero sizes, and delete all temporary files before returning ready. It must not persist PPTX artifacts, run LibreOffice, create proof bundles, map charts/tables/images/theme/brand, perform visual QA, or claim production-quality output.


Implementation note after KR-7H.10:

KR-7H.10 adds `presentation_renderer_worker_pptx_artifact_bundle.v1` and `presentation_renderer_worker_render_report.v1`. It writes a persistent PPTX artifact and deterministic render report JSON into an explicit controlled renderer-worker output directory using only the previously allowed title/body mapping from validated renderer input / source-backed dry-run payloads. KR-7H.10 still has no LibreOffice PDF/PNG proof, no proof bundle, no visual QA/scoring, no chart/table/image/theme/brand/professional layout mapping, no frontend changes, no GigaChat/runtime changes, and no production-quality or Kimi-level output claim.

### KR-7H.10 persistent PPTX artifact bundle + render report contract

KR-7H.10 is the persistent artifact-bundle step in the consolidated KR-7H plan. It may create a controlled PPTX artifact bundle and render report contract, but it must not run LibreOffice, generate proof images, produce proof bundles, broaden renderer mapping beyond title/body text, or claim production renderer closure. Validation must include exact package self-test, `kw_renderer_worker_pptx_artifact_bundle_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification.


KR-7H.12 renderer hardening adds `presentation_renderer_worker_source_image_hardening.v1` to enforce source-image-only fail-closed renderer input guardrails and to forbid fake/generated/fallback image artifacts without implementing image mapping or source image selection runtime.

Implementation note after KR-7H.13:

KR-7H.13 adds `presentation_renderer_worker_kr7h_closure_gate.v1` as the KR-7H closure gate. It records that the KR-7H renderer-worker foundation layers KR-7H.1 through KR-7H.12 are present and covered by project-resident checks, but it does not claim production renderer closure, visual QA/scoring, Kimi-level quality, source image selection, image mapping, professional layout, UI changes, GigaChat/runtime changes, or Docker/deploy/Postgres behavior changes.

KR-7H.13 is validated by `kw_renderer_worker_kr7h_closure_gate_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. After KR-7H.13 is closed, the next phase is KR-7I template and brand understanding.

Implementation note after KR-7I:

KR-7I adds `presentation_template_brand_profile.v1` and `kw_template_brand_profile_check.py` as the first template and brand understanding contract after KR-7H closure. The implementation inspects uploaded PPTX templates as OOXML/ZIP packages and builds a deterministic template profile with slide size, theme colors, fonts, masters/layouts/placeholders, source media asset metadata, role-to-layout-family hints, and unsupported-feature warnings. It does not implement `no_template_clone_rewrite_mode` as a generation path, does not copy old template text/content, does not implement the no_production_layout_engine, does not change renderer runtime, does not perform visual QA/scoring, does not select source images for user decks, and does not claim Kimi-level quality.

KR-7I is validated by the template brand profile checker, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. The next phase is KR-7J source image selection.

### KR-7J source image selection contract

KR-7J introduces `presentation_source_image_selection.v1` for deterministic, source-backed image selection from uploaded document assets and uploaded PPTX template media. Each selected image must carry citation/provenance/checksum evidence. Generated, random, fake, inline, external, or fallback image artifacts are forbidden as success evidence; if no relevant image exists, the slide must remain typographic or diagrammatic. KR-7J does not implement renderer image placement, source image runtime UI, visual QA/scoring, production layout, GigaChat/runtime, Docker/deploy/Postgres behavior, or Kimi-level quality claims.
