# KR-4A Workflow Contract Core

KR-4A introduces a shared workflow contract core for the mandatory KW Studio product workflows.
It is not a full runtime rewrite. It is the foundation that future runtime work must implement against.

The core product workflows are:

```text
docx
pdf
xlsx
slides
python_analysis
browser_evidence
```

The contract core makes every workflow describe the same product concerns:

```text
WorkflowInput
WorkflowPlan
WorkflowRun
WorkflowArtifact
WorkflowManifest
WorkflowQualityReport
WorkflowProvenance
```

## Why this exists

Earlier workflow contracts were useful, but they mixed historical stage names with product behavior.
KR-4A creates a product-facing contract vocabulary for offline/intranet, artifact-first, provenance-first workflows.

The goal is to make future implementation work consistent:

```text
source files + user intent
-> workflow plan
-> controlled tools
-> artifact bundle
-> manifest
-> quality report
-> provenance/evidence
-> operator diagnostics
-> restore/audit metadata
```

## Contract rules

Every mandatory workflow must be offline-ready and operator-gated.
Every mature workflow must produce required artifacts, manifests, quality reports, and source evidence.
Quality checks must fail closed rather than silently accepting missing or corrupt outputs.

Required manifest files:

```text
artifact_manifest.json
quality_report.json
source_evidence_manifest.json
```

Slides additionally require citation and visual QA artifacts.
XLSX additionally requires workbook metadata, formula inventory, and table previews.
Python analysis additionally requires the executed script, result JSON, and execution log.
Browser evidence additionally requires approved capture scope, screenshots, captured pages, and evidence manifests.

## Checker

The machine-checkable guardrail is:

```bash
python scripts/kw_workflow_contract_core_check.py --repo-root . --require-ready
```

It validates the contract registry in:

```text
backend/app/workflows/core_contracts.py
```

The production readiness gate also runs this checker so future patches cannot accidentally drop the KR-4A contract foundation.
