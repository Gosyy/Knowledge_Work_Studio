# P9-4 Visual QA semantic review guard from human review

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `1f546bb46de3f11f1a0a12f185bdcb1800632b18`
- Kimi-level claimed: `False`

## Purpose

P9-4 addresses a remaining P9-1B human-review gap: visual QA could report a high score for artifacts that were visually clean but still not product-quality. The human review showed examples where a deck received visual QA score 100 while reviewers still requested rework for generic fallback labels, raw CSV/table rendering, arbitrary Current/Target layouts, weak review placeholders, and missing semantic status coverage.

P9-4 keeps the scope narrow. It extends the local deterministic visual QA runtime with semantic/product-quality red-flag checks derived from P9 human-review findings. It does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet requirements, or Kimi-level claims.

## Runtime behavior

The visual QA runtime now adds P9-4 semantic issues when the approved plan/render intent still contains known review red flags:

- generic fallback labels such as `K1 Plan`, `Key point`, or `Additional source-grounded planning point`;
- raw CSV/table header rendering such as `Option,Strength,Weakness,Recommendation`;
- arbitrary `Current / Option A` versus `Target / Option B` comparison labels;
- generic table `Review` placeholder cells;
- status-deck content that needs explicit operator review for K4/K5/K6, closure, risks, and next actions.

Blocker semantic findings can prevent a visually clean artifact from being marked as passed. Warning semantic findings request operator review.

## Safe metadata

P9-4 adds safe metadata flags and counts:

- `p9_4_visual_qa_semantic_guard_supported`;
- `visual_qa_product_quality_guard_supported`;
- `visual_qa_semantic_issue_detection_supported`;
- `visual_qa_human_review_alignment_supported`;
- `semantic_review_guard_issue_count`;
- `semantic_review_guard_warning_count`;
- `semantic_review_guard_blocker_count`.

The metadata remains safe: raw source text, raw prompt text, raw slide text, and secret-like values are not stored. The patch remains offline/local and deterministic.

## Acceptance

P9-4 is accepted only when:

- `scripts/kw_p9_4_visual_qa_semantic_guard_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py` passes;
- prior P9-2/P9-3 and RCH3/K4 checks remain ready;
- production readiness `--checks-only` includes the P9-4 files;
- after commit and push, the full runner and Docker smoke pass.

P9-4 does not claim whole-project Kimi-level parity. It is a targeted product-release hardening patch derived from conservative human review findings.

## P9-4 hotfix follow-up

The full runner exposed two bounded integration issues after the initial targeted acceptance: P9-4 semantic issues introduced warning/info issue objects into K6 operator approval paths that expected a stable `issue_id`, and the raw CSV/header guard was too broad for natural decision-matrix language such as “compare each option by strength, weakness, and recommendation”.

The hotfix keeps the semantic guard intact while adding a backward-compatible `issue_id` alias for visual QA issues and narrowing raw CSV detection to actual header/table signatures. It does not add APIs, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.
