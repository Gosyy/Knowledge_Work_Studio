# KW Studio Quality Matrix

## Purpose

This matrix keeps the whole product visible. Slides are high priority, but KW Studio remains a multi-workflow, artifact-first, provenance-first knowledge-work studio.

Status values:

```text
Implemented        runtime/checker exists and is actively validated
Partial            important pieces exist but product behavior is incomplete
Planned            roadmap exists but runtime is not mature
Blocked            known blocker prevents acceptance
Deprecated         historical surface only
Needs verification current implementation must be re-audited before claims
```

## Workflow matrix

| Workflow | Inspect | Generate | Validate | Bundle | Provenance | Render / QA | UI visibility | Current status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DOCX | Planned | Planned | Planned | Planned | Planned | Planned | Partial | Needs verification | Mandatory pillar; future work must align with workflow contract core. |
| PDF | Planned | Planned | Planned | Planned | Planned | Planned | Partial | Needs verification | Mandatory pillar; source-grounded extraction/evidence must remain honest. |
| XLSX / CSV | Implemented | Planned | Implemented | Implemented | Implemented | Not applicable | Partial | Partial | KR-5A/KR-5B added inspect and bundle validation; no destructive editing or complete Excel coverage claim. |
| Slides | Implemented | Partial | Partial | Implemented | Partial | Implemented | Partial | Partial | KR-6D validates/repairs GigaChat planning; KR-7 targets professional PresentationIR, source assets, data-backed charts, template rewrite, and quality gates. |
| Python analysis | Planned | Planned | Planned | Planned | Planned | Planned | Partial | Needs verification | Must remain controlled, deterministic, logged, and artifact-backed. |
| Browser evidence | Planned | Planned | Planned | Planned | Planned | Planned | Partial | Needs verification | Must remain operator-gated and evidence/provenance-first, not autonomous browsing. |

## Cross-workflow quality rules

Every mature workflow must define:

```text
input contract;
workflow plan;
artifact outputs;
artifact manifest;
quality report;
source evidence or provenance manifest;
operator diagnostics;
fail-closed validation behavior;
profile-neutral tests and runners.
```

## Documentation maintenance rule

When a patch changes workflow maturity, validation behavior, artifact bundle expectations, provenance coverage, render/QA behavior, or UI visibility, update this matrix in the same patch.
