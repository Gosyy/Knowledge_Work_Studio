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
| Slides | Implemented | Partial | Partial | Implemented | Partial | Implemented | Partial | Partial | KR-6D validates/repairs GigaChat planning; KR-7B locks GigaChat-only runtime scope; KR-7C.1 adds API-first /api/v1 Presentation contract skeleton; KR-7C.2 adds PresentationIR versioning/persistence contract; KR-7C.3 adds source attachment/read metadata contract; KR-7D.1 adds offline source ingestion foundation for DOCX/PPTX/XLSX/CSV/Markdown/text with provenance manifests and source asset registry reports; KR-7D.2 adds SourceAssetRegistry persistence for extracted assets with checksum-verified relative-path storage manifests; KR-7D.3 enriches document structure extraction with source_structure.v1 elements and chart candidates for DOCX/PPTX/XLSX/PDF/Markdown without evidence retrieval; KR-7D.4 hardens real package extraction fidelity with OOXML relationship resolution, dependency status metadata, and relationship-aware media assets; KR-7E.1 adds offline evidence index foundation with lexical/BM25-like scoring, provenance refs, and unsupported-claim guardrails; KR-7E.2 hardens section scoring, claim-term coverage, missing-term reporting, and structured unsupported-claim reports; KR-7E.3 adds evidence index persistence and retrieval API read contract with safe manifests and read-only /api/v1 evidence endpoints; KR-7F.1 adds PresentationIR planner foundation with deterministic evidence-bound drafts, explicit degraded/blocked states, and no final GigaChat planner runtime claim; KR-7F.2 hardens evidence-aware slide outline planning with presentation_ir_outline.v1, coverage summaries, missing-term slide warnings, and explicit unsupported outline states; KR-7F.3 hardens planner snapshot persistence/API metadata; KR-7G.1 adds visual grammar library foundation with presentation_visual_grammar.v1 editable block specs and validators; KR-7G.2 binds visual grammar blocks; KR-7G.2 binds presentation_visual_grammar.v1 blocks into PresentationIR planner output through presentation_ir_visual_grammar_binding.v1; KR-7G.3 exposes read-only visual grammar catalog and binding validation APIs with renderer_runtime_implemented=false while PDF extraction remains dependency-gated and honest. |
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

KR-7F.3 hardens planner persistence and PresentationIR snapshot API contract with presentation_ir_planner_snapshot.v1 metadata, blocked-result fail-closed persistence, and read-side planner snapshot exposure.

KR-7G.3 exposes visual grammar read contracts without renderer claims: catalog and binding validation APIs are implemented, but rendered PPTX visual output remains a later phase.

KR-7H.1 adds renderer worker boundary contract preflight for Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle without production PPTX renderer claims. It keeps renderer_runtime_implemented=false and declares future artifact/proof bundle contracts without producing them.

KR-7H.2 adds renderer worker dry-run scaffold contract for validating PresentationIR -> renderer-worker input -> invocation manifest without Node/PptxGenJS or LibreOffice runtime. It keeps renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false while making unsupported input fail closed.

KR-7H.3 adds renderer worker protocol preflight scaffold without PptxGenJS rendering or LibreOffice proof runtime. It validates the KR-7H.2 dry-run report and invocation manifest through a deterministic Node-side preflight script while keeping renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false.
KR-7H.4 adds isolated renderer worker package preflight without PptxGenJS dependency or PPTX runtime. It declares presentation_renderer_worker_package_preflight.v1, validates package scripts and frontend isolation, and keeps renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false.

KR-7H.5 adds controlled PptxGenJS capability preflight inside the isolated renderer_worker package without PPTX generation or LibreOffice proof runtime. It pins `pptxgenjs@4.0.1` only in the renderer_worker package, validates dependency availability/version with `presentation_renderer_worker_pptxgenjs_capability.v1`, and keeps renderer_runtime_implemented=false, production_pptx_output_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false.
