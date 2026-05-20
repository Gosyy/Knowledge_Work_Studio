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
Ollama or other local models are development or fallback paths unless separately accepted.

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
