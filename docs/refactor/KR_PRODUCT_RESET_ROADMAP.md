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
