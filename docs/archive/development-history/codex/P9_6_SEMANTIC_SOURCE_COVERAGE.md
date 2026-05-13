# P9-6 Semantic source coverage from human review

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `a126bcb33cfc94441d6d0edf41ee90edfccc041f`
- Kimi-level claimed: `False`

## Purpose

P9-6 addresses the human-review finding that technical provenance coverage can be complete while semantic source coverage is still incomplete for the deck's review purpose.

P9-2 hardened fallback planning, P9-3 hardened renderer layout selection, P9-4 added a visual-QA semantic guard, and P9-5 made provenance evidence more useful for operators. P9-6 adds a deterministic semantic coverage section to the existing K5 provenance manifest so late source signals such as K4, K5, K6, closure/readiness, risks, next actions, decision matrix needs, and offline topology are not hidden behind complete slide-link coverage.

## Runtime behavior

The local K5 provenance runtime now emits `semantic_source_coverage` in the manifest. The section contains bounded signal identifiers and aggregate coverage counts only. It does not store raw source text, raw prompt text, or secret-like values.

The semantic guard is deliberately conservative. It does not invent content, does not call a cloud LLM, and does not block generation by itself. Instead, it marks `human_semantic_coverage_review_required` when source signals are expected but not reflected in slide titles/bullets/layout hints.

## Safe metadata

P9-6 adds aggregate safe metadata flags:

- `p9_6_semantic_source_coverage_supported`;
- `semantic_source_signal_coverage_supported`;
- `late_source_section_guard_supported`;
- `human_semantic_coverage_review_supported`;
- `semantic_source_expected_signal_count`;
- `semantic_source_covered_signal_count`;
- `semantic_source_uncovered_signal_count`;
- `semantic_source_coverage_status`;
- `human_semantic_coverage_review_required`.

Raw source text and raw prompt text remain excluded from safe metadata.

## Scope guard

P9-6 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, hidden public internet runtime requirements, or Kimi-level claims.

## Acceptance

P9-6 is accepted only when:

- `scripts/kw_p9_6_semantic_source_coverage_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_6_semantic_source_coverage.py` passes;
- previous P9-2/P9-3/P9-4/P9-5 checkers remain ready;
- K5/RCH2/K6 checks remain ready;
- production readiness `--checks-only` includes the P9-6 files;
- after commit and push, the full runner and Docker smoke pass on profile 2.
