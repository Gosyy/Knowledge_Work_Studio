# S-phase — Kimi Slides-class workflow roadmap

- status: `controlled_kimi_slides_class_roadmap`
- branch: `9_Product_Release_Hardening`
- starts after: `P10-11 final operator release closure`
- Kimi-level claimed: `False`

## Purpose

S-phase moves KW Studio from release-approved operator-grade document-to-artifact workflows toward Kimi Slides-class workflow quality under offline/intranet constraints.

The target is not an unrestricted public-cloud Kimi clone. The target is selected workflow parity for offline/intranet deployments: source ingestion, outline-first UX, editable plan, adaptive deck modes, native PPTX visuals, template support, screenshot/image workflows through local heavy modules, internal citations, conversational edits, render-based visual QA, and expanded benchmark review.

## Phase roadmap

1. `S1` — Kimi Slides-class gap dossier.
2. `S2` — Outline-first frontend workflow.
3. `S3` — Adaptive deck modes.
4. `S4` — Native table/chart/diagram rendering.
5. `S5` — Template and slide-master ingestion.
6. `S6` — Image/screenshot to slide workflow.
7. `S7` — Offline/intranet research citations.
8. `S8` — Conversational edit loop.
9. `S9` — Render-based visual QA.
10. `S10` — Expanded Kimi-style benchmark and human review.

## Evidence boundary

S-phase must not claim `Kimi-level achieved` until a dedicated benchmark and human review support a narrower evidence-backed claim. The preferred future wording is:

```text
Kimi Slides-class offline workflow parity for selected benchmark scenarios.
```

## Offline/intranet boundary

The production target remains offline/intranet. Public API GigaChat evidence remains accepted release evidence for the current project completion path, but it is not Server 3 local-intranet proof.

Server 3 `local_intranet` operator readiness can be prepared in S-phase without claiming live verification unless a real Server 3 endpoint is tested.

## S2 checkpoint

S2 closes the first execution checkpoint of the S-phase roadmap: outline-first frontend workflow. The accepted contract is source intake -> outline draft -> editable plan review -> explicit plan approval -> render mode selection -> generation from the approved plan -> artifact history -> plan snapshot -> retry from saved plan.

This is not Kimi Slides-class parity. It is the frontend-facing workflow foundation required before S3 adaptive deck modes and later visual/rendering improvements.

## S3 execution checkpoint

S3 implements the adaptive deck mode registry needed after S2 outline-first workflow. The accepted modes are `executive_board_deck`, `architecture_review_deck`, `project_status_deck`, `decision_matrix_deck`, and `long_document_explainer`.

S3 prepares S4 native table/chart/diagram rendering and S9 render-based visual QA by recording mode-specific slide archetypes, table/chart policies, visual QA expectations, provenance expectations, and known failure guards. It is still not Kimi Slides-class parity.

## S4 execution checkpoint

S4 accepts native table/chart/diagram rendering as a registry and contract layer. It binds native PPTX tables, charts, and shape diagrams to the S3 adaptive deck modes so later implementation can render decision matrices, topology diagrams, timelines, risk tables, and evidence packages without raster-only fallbacks.

S4 remains offline/intranet-compatible and does not claim Kimi Slides-class parity. The next controlled step is `S5 — template and slide-master ingestion`.

## S5 execution checkpoint

S5 accepts local/offline template and slide-master ingestion as a contract layer. It extracts bundled template metadata, maps S3 deck-mode archetypes and S4 native visuals to local slide layouts, and rejects external template references.

S5 keeps the production target offline/intranet, does not use cloud template discovery, and does not claim Kimi Slides-class parity. The next controlled step is `S6 — image/screenshot-to-slide workflow`.

## S6 acceptance note

S6 turns the roadmap item `Image/screenshot to slide workflow` into a controlled offline-safe contract. The accepted scope is local image/screenshot ingestion, local heavy-module OCR/layout/region metadata, editable PPTX reconstruction preference, raster fallback only with an explicit reason, and source-to-region-to-slide provenance.

S6 keeps Kimi Slides-class as a future benchmark target, not a current parity claim.


## S7 - Offline/intranet research citations

S7 turns source-grounded evidence into a first-class offline/intranet citation manifest. Slide-level claims, S4 native visuals, and S6 image-region reconstructions must link to uploaded documents, internal browser evidence packets, local knowledge-base entries, intranet documents, image regions, or generated artifact manifests.

S7 explicitly forbids hidden public-web lookups, cloud research, cloud vision, and unattributed model memory as production-default citation sources. The next phase is S8 conversational edit loop over saved plans and citation-aware revisions.
