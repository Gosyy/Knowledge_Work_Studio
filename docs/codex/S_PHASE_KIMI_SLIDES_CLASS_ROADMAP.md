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

## S8 checkpoint — Conversational edit loop

S8 turns the S2 saved-plan workflow and S7 citation manifest into a controlled conversational revision loop. Operators can request revisions such as shortening a deck, reframing it for a board audience, adding a risk slide, replacing a table with a decision matrix, revising slide order, tightening citations, or converting a saved plan into an architecture-review deck.

Every S8 revision must load a saved plan snapshot, produce a reviewable plan patch, require explicit operator approval, preserve plan lineage, revalidate citations, and generate from the revised approved plan. Hidden public web research, cloud vision, transient-prompt-only generation, and Kimi-level claims remain out of scope.
### S9 acceptance expansion

S9 is accepted when render-based visual QA requires actual local render evidence and geometry manifests, detects overlap/clipping/tiny text/table overflow/diagram collisions, links checks to S4/S6/S7/S8 evidence, and preserves offline/intranet boundaries without claiming Kimi-level parity.

## S10 checkpoint

S10 defines the expanded Kimi-style benchmark and human-review contract for selected offline/intranet workflow parity scenarios.

The benchmark scope contains twelve scenarios and requires the full S1-S9 evidence chain. A future parity claim is allowed only after completed benchmark execution and real human review. The only permitted scoped claim wording is:

```text
Kimi Slides-class offline workflow parity for selected benchmark scenarios.
```

S10 does not claim whole-project Kimi-level parity, does not verify Server 3 `local_intranet`, and does not add hidden public-internet production dependencies.
## S11 — S-phase closure dossier

S11 closes the S1-S10 capability foundation. It records that the product now has controlled contracts for outline-first workflow, adaptive modes, native visuals, template/master ingestion, image-to-slide workflow, offline citations, conversational edits, render-based visual QA, and an expanded 12-scenario benchmark.

S11 does not claim completed Kimi Slides parity. The only accepted future wording remains `Kimi Slides-class offline workflow parity for selected benchmark scenarios`, and that wording requires future completed benchmark execution plus real human review results.

## S12 — Selected benchmark execution packet / human review workflow

S12 converts the S10 benchmark contract and S11 closure dossier into an execution-ready review packet workflow. It requires 12 scenario packets, evidence manifests, review worksheets, reviewer instructions, and an ingest schema while preserving the claim boundary: no selected parity claim without future completed results and real human review.

## S13a - Selected benchmark review packet skeleton

S13a creates the execution/review packet skeleton for all 12 S10 scenarios. It prepares packet indexes, evidence-manifest skeletons, worksheet skeletons, reviewer instructions, operator handoff notes, and review-result ingest schema boundaries.

S13a intentionally does not run live GigaChat. S13b is the controlled phase for `public_api_dev` generation of real artifacts.
## S13b — live public_api_dev GigaChat generation workflow

S13b prepares and validates the live GigaChat `public_api_dev` execution workflow for the twelve selected benchmark scenarios. It is intentionally separated from default full-runner readiness so normal offline/intranet checks do not require secrets or internet access.

Accepted future claim wording remains gated by completed S10/S12/S13 evidence and human review: `Kimi Slides-class offline workflow parity for selected benchmark scenarios.`

## S13c — live GigaChat evidence packet export

S13c packages S13b live public_api_dev GigaChat artifacts into review-ready evidence packets and pending human-review worksheets. It is a handoff/export stage, not a review-completion or parity-claim stage.

## S13d — Live benchmark prompt/schema hardening and rerun

S13d upgrades the selected benchmark live rerun path from generic plan generation to strict scenario-specific JSON output: at least eight slides per scenario, native visual plans, citation manifests, render QA obligations, evidence manifest fields, and human review handoff. The route remains `public_api_dev`; no Server 3 production proof or selected parity claim is implied.

## S13e — Hardened output repair/parser

Status: targeted implementation stage.

S13e adds deterministic repair and revalidation for failed S13d hardened live outputs. It does not call GigaChat again, does not fabricate human review results, and does not support any selected parity claim by itself.

## S13f — strict per-scenario JSON rerun

S13f hardens the selected benchmark execution path after S13e repair remained below acceptance. It adds strict per-scenario JSON schema echo, fail-fast validation, and deterministic repair fallback for syntax only. It does not claim selected parity, Kimi-level, or Server 3 local_intranet verification.

## S13g — canonical schema adapter + minimal strict rerun

Status: controlled workflow added.

The S13g path replaces large strict schema prompting with a minimal prompt plus canonical adapter. The adapter must preserve provenance for model-provided versus adapter-added fields and keep human review pending until real completed worksheets are ingested.

## S13h — Targeted retry for failed S13g scenarios

S13h adds a targeted retry stage after S13g. The stage is intended to avoid wasting live calls on already canonical-valid scenarios and to merge reused canonical-valid outputs with newly retried failed outputs. A merged result can proceed to evidence packet export only if all 12 selected scenarios are canonical-valid after merge.

## S13i — single-scenario executive memo retry

Status target: controlled patch-stage plus later live execution. S13i uses the latest S13h 11/12 ZIP as input, retries only `executive_memo_to_board_deck`, and accepts the result only if the merged canonical output count becomes 12/12. Review worksheets remain `pending_human_review`.

## S13j deterministic executive memo salvage

S13j is a narrow deterministic recovery step after S13i live retry left `executive_memo_to_board_deck` malformed while eleven selected scenarios remained canonical-valid. S13j does not call GigaChat; it salvages the failed S13i response, preserves source digests, marks salvage-generated fields as not model-generated, and keeps human review pending. It does not support selected parity, Kimi-level, or Server 3 `local_intranet` claims by itself.

## S13k human review packet export from S13j merged artifacts

Status target: controlled patch-stage plus live packet export from the S13j 12/12 ZIP. S13k creates human review worksheets, evidence manifests, canonical response copies, and S13j provenance files. The executive memo worksheet must preserve the deterministic fallback adapter warning so reviewers can distinguish salvage-generated fields from model-generated content. Review remains pending until real completed worksheets are ingested.
