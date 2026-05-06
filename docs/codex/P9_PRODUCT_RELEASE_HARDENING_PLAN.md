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
