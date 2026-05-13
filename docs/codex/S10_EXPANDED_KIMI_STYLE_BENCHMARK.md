# S10 — Expanded Kimi-style benchmark and human review

- status: `controlled_expanded_kimi_style_benchmark_contract`
- branch: `9_Product_Release_Hardening`
- baseline before S10: `e2954d5e9d837571567c14b184cbc5dcebe86a7f`
- Kimi-level claimed: `False`

## Purpose

S10 closes the S-phase capability build-out with an expanded Kimi Slides-class benchmark and human-review contract.

S10 does **not** claim Kimi-level parity by itself. It defines the scenarios, required evidence, automated outputs, render-based visual QA, citation coverage, and human-review acceptance policy that a later real benchmark execution must satisfy before the project may make a narrow evidence-backed claim.

The only future claim wording S10 allows is:

```text
Kimi Slides-class offline workflow parity for selected benchmark scenarios.
```

## Benchmark scenarios

S10 requires twelve selected offline/intranet scenarios:

1. `executive_memo_to_board_deck`
2. `architecture_doc_to_architecture_review`
3. `project_log_to_status_deck`
4. `comparison_table_to_decision_matrix`
5. `long_doc_to_structured_explainer`
6. `research_report_to_cited_deck`
7. `kpi_spreadsheet_to_business_review`
8. `product_launch_brief_to_launch_deck`
9. `training_material_to_training_deck`
10. `screenshot_to_editable_slide`
11. `branded_template_to_brand_deck`
12. `browser_evidence_packet_to_cited_deck`

These scenarios map back to the S1 gap dossier and to the S2-S9 controls: outline-first workflow, adaptive modes, native visuals, local templates, image/screenshot reconstruction, offline citations, conversational edits, and render-based visual QA.

## Required evidence per scenario

Each scenario must produce:

- approved plan snapshot;
- generated PPTX;
- artifact manifest;
- safe metadata;
- citation manifest;
- render geometry manifest;
- render-based visual QA report.

The evidence must remain offline/intranet-safe. Hidden public web lookup, cloud search, cloud vision, remote screenshot services, and unattributed model memory are not valid benchmark evidence.

## Human review policy

S10 requires real completed human review before any selected parity claim is supported.

The human review must score:

- storyline quality;
- source grounding;
- layout visual quality;
- native visual editability;
- citation usefulness;
- operator workflow fit.

The selected parity threshold is intentionally conservative:

- at least 10 of 12 scenarios approved;
- zero rejects;
- zero blocker visual defects;
- zero `request_rework` scenarios for the final selected parity claim;
- complete slide-claim citation coverage;
- complete native-visual citation coverage;
- complete render-based visual QA pass for accepted scenarios.

## Boundaries

S10 does not add public API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or hidden public-internet production dependency.

S10 does not verify Server 3 `local_intranet`. Production/offline mode remains the target deployment mode.

S10 does not allow the phrase `Kimi-level achieved` as a project-wide claim. A later claim must remain scoped to selected benchmark scenarios and must be backed by real completed benchmark results and human review.

## Acceptance

S10 is accepted when:

```bash
python scripts/kw_s10_kimi_style_benchmark_check.py --repo-root . --require-ready --json
python -m pytest backend/tests/smoke/test_s10_kimi_style_benchmark.py -q
```

both pass, production readiness includes the S10 checkpoint, and full runner plus Docker smoke pass after commit and push.
