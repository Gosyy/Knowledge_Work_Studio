# P9 Product Release Hardening Plan

P9 starts from the accepted K/RC/RCH baseline on branch `8_K_Phase` at `a2f1aa90fbc56531de85a953447f61a52a63efb7`.

P9 is not a new product-runtime phase by default. It is a release-hardening track for evidence, human review, production topology verification, and focused quality fixes derived from accepted benchmark findings.

## Accepted source baseline

- K0-K6 closed.
- K-phase closure closed.
- RC1-RC5 accepted.
- RCH1-RCH4 accepted.
- KRC final branch closure accepted.

## P9-1 — Golden benchmark human review results

P9-1 captures completed human review results for the five golden benchmark artifacts generated from the closed K/RC/RCH baseline.

The review results are intentionally conservative: all five generated decks are marked `request_rework`. This does not mean the runtime failed. It means the decks are not yet strong enough for product-quality claims because they still show generic fallback labels, weak decision-table treatment, incomplete semantic coverage in some cases, and evidence/provenance usability gaps.

## Scope guard

P9-1 does not add product runtime logic, API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.

## Next hardening direction

The first follow-up patch should be selected from tracked human-review findings, preferably renderer/planning hardening for generic fallback labels, comparison-table decision matrix handling, and filler-slide prevention.

## P9-2 — Renderer/content hardening from human review

P9-2 implements the first focused quality hardening patch from P9-1B findings. It improves deterministic fallback planning for renderer-facing content without adding APIs, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.

The patch targets four conservative findings: removal of generic fallback labels, comparison-table decision-matrix handling, project-log late-phase coverage, and filler-slide prevention for long structured sources. Acceptance is tracked by `scripts/kw_p9_2_renderer_content_hardening_check.py` and `backend/tests/smoke/test_p9_2_renderer_content_hardening.py`.

## P9-3 — Renderer layout hardening from human review

P9-3 starts from accepted P9-2 on branch `9_Product_Release_Hardening` at `36bd460f605ad9dec532825f1820983657ebe5d4`. It targets the renderer/template portion of P9-1B findings that remained after P9-2 planning hardening.

The patch removes arbitrary synthesized `Current / Option A` and `Target / Option B` renderer labels, replaces generic `Review` placeholder data cells with source-derived operator-use columns, preserves title/section/conclusion layout roles before semantic promotion, and renders comparison-table decision matrices as runtime options versus decision criteria. Acceptance is tracked by `scripts/kw_p9_3_renderer_layout_hardening_check.py` and `backend/tests/smoke/test_p9_3_renderer_layout_hardening.py`.

## P9-4 — Visual QA semantic review guard from human review

P9-4 starts from accepted P9-3 on branch `9_Product_Release_Hardening` at `1f546bb46de3f11f1a0a12f185bdcb1800632b18`. It targets the human-review gap where visual QA could report a clean visual result while generated decks still contained product-quality blockers such as generic fallback labels, raw CSV/table rendering, arbitrary Current/Target synthesis, or generic table review placeholders.

The patch adds a deterministic semantic/product-quality guard inside the local visual QA runtime. It can downgrade visually clean artifacts to operator review or blocked status when plan/render content contains known P9 human-review red flags. Acceptance is tracked by `scripts/kw_p9_4_visual_qa_semantic_guard_check.py` and `backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py`.

## P9-5 — Provenance usefulness hardening from human review

P9-5 starts from accepted P9-4 hotfix on branch `9_Product_Release_Hardening` at `647342bc420192bdf0267ef7ac31344eec786daa`. It targets the remaining P9-1B evidence/provenance usefulness finding: technically complete source coverage was not yet sufficient for fast human validation.

The patch adds deterministic operator evidence cards to the local source-to-slide provenance manifest. Each card links a slide claim preview, bounded evidence excerpt, match score, usefulness score, review priority, and operator hint without storing raw source text in safe metadata. Acceptance is tracked by `scripts/kw_p9_5_provenance_usefulness_check.py` and `backend/tests/smoke/test_p9_5_provenance_usefulness.py`.

## P9-6 — Semantic source coverage from human review

P9-6 starts from accepted P9-5 on branch `9_Product_Release_Hardening` at `a126bcb33cfc94441d6d0edf41ee90edfccc041f`. It targets the human-review gap where technical provenance coverage can be complete while later semantic source sections are still missing from the generated deck.

The patch adds a deterministic semantic coverage section to the local K5 provenance manifest. It tracks bounded signal identifiers for late source coverage such as K4 visual QA, K5 provenance, K6 workflow, closure/readiness, risks, next actions, decision matrix needs, and offline topology. Acceptance is tracked by `scripts/kw_p9_6_semantic_source_coverage_check.py` and `backend/tests/smoke/test_p9_6_semantic_source_coverage.py`.

## P9-7 — Golden benchmark post-hardening review readiness

P9-7 starts from accepted P9-6 on branch `9_Product_Release_Hardening` at `0879dfd81b00db67ea20a15cb326c44c17849984`. It targets the post-hardening review-readiness gap after P9-2 through P9-6: the original golden benchmark human-review findings now have hardening evidence, but no approval state should be changed without a new operator review.

The patch adds a deterministic evidence-only review-readiness checker. It maps the five original `request_rework` golden benchmark cases to P9-2/P9-3/P9-4/P9-5/P9-6 hardening evidence and keeps every case marked for future human re-review. Acceptance is tracked by `scripts/kw_p9_7_golden_review_readiness_check.py` and `backend/tests/smoke/test_p9_7_golden_review_readiness.py`.

P9-7 also classifies full-runner warnings explicitly: deprecated transitive npm packages, npm audit vulnerability summaries, and RC2 quality-review `warning_findings` are known non-blocking warnings for this evidence patch. Dependency/security remediation remains a separate controlled track, and P9-7 does not run `npm audit fix --force` or change dependency versions.

## P9-8 — Product release hardening closure dossier

P9-8 starts from accepted P9-7 warning classification on branch `9_Product_Release_Hardening` at `c1f6735a21fa82d13e2638d7b20ee304911275ab`. It closes the P9 release-hardening evidence track without changing runtime behavior or approval state.

The patch adds a deterministic closure dossier and checker that require P9-1 through P9-7 evidence to remain present, keep all five original golden benchmark cases queued for human re-review, preserve known non-blocking warning classification, and keep dependency/security remediation as a separate controlled track. Acceptance is tracked by `scripts/kw_p9_8_product_release_hardening_closure_check.py` and `backend/tests/smoke/test_p9_8_product_release_hardening_closure.py`.

## P10 - Post-P9 golden benchmark regeneration and human re-review

P10 starts from accepted P9-8 on branch `9_Product_Release_Hardening` at `42d999a93a6328c1f35e8e3118b6bca6ab3f45ca`. It is the validation phase after the P9 hardening evidence track.

P10-1 adds a post-P9 regeneration-readiness checkpoint. It does not regenerate artifacts by itself and does not change approval state. It verifies that the five original P9-1B `request_rework` golden cases, the RC1 golden benchmark harness, and the P9 closure evidence are present so a post-P9 artifact pack can be generated and sent through human re-review.

P10-1 keeps known full-runner warnings classified as non-blocking for this evidence checkpoint, defers dependency/security remediation to a separate controlled track, does not run `npm audit fix --force`, and makes no Kimi-level claim. Acceptance is tracked by `scripts/kw_p10_1_post_p9_regeneration_readiness_check.py` and `backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py`.
