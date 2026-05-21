# P9-3 Renderer layout hardening from human review

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `36bd460f605ad9dec532825f1820983657ebe5d4`
- Kimi-level claimed: `False`

## Purpose

P9-3 starts after accepted P9-2. P9-2 fixed source-aware deterministic planning and removed generic fallback planning labels. Human-review findings still showed renderer-level issues: arbitrary `Current/Target` comparison labels, generic `Review` placeholder data cells, and title/conclusion slides being promoted into data-summary layouts by broad heuristics.

P9-3 keeps scope narrow: it hardens deterministic renderer layout selection and synthesized slide blocks. It does not add APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or hidden public internet runtime requirements.

## Human-review findings addressed

P9-3 addresses the remaining renderer/template portion of the P9-1B findings:

- comparison slides should not use arbitrary `Current / Option A` and `Target / Option B` labels;
- data-summary tables should not use generic `Review` placeholder cells;
- comparison-table decision decks should preserve runtime options and decision criteria as renderer blocks;
- title, section, conclusion, and appendix slides should preserve their structural layout roles before semantic promotion.

## Runtime behavior

The K3/RCH1 renderer quality pass now applies a P9-3 normalization layer before deterministic PPTX rendering:

- structural slide roles are selected before semantic data/comparison promotion;
- `Decision matrix` comparison slides create `Runtime options` versus `Decision criteria` renderer blocks;
- prefixed decision evidence such as `Strength`, `Weakness`, and `Recommendation` becomes a source-derived table with `Dimension`, `Evidence`, and `Operator use` columns;
- old synthesized RCH1 comparison/table labels are normalized if they appear in an incoming plan.

## Safe metadata

P9-3 adds safe renderer metadata flags:

- `p9_3_renderer_layout_hardening_supported`;
- `p9_3_case_aware_layout_selection_supported`;
- `p9_3_arbitrary_current_target_labels_removed`;
- `p9_3_generic_review_placeholder_removed`;
- `p9_3_decision_matrix_renderer_blocks_supported`.

The metadata remains safe: raw source text, raw prompt text, and secret-like values are not stored. Kimi-level and whole-project parity claims remain explicitly unsupported.

## Acceptance

P9-3 is accepted only when:

- `scripts/kw_p9_3_renderer_layout_hardening_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_3_renderer_layout_hardening.py` passes;
- previous P9-2, RCH1, and K3 checks still pass;
- production readiness `--checks-only` includes the P9-3 files;
- after commit and push, the full runner and Docker smoke pass.

P9-3 does not claim whole-project Kimi-level parity. It is a targeted product-release hardening patch derived from conservative human review findings.
