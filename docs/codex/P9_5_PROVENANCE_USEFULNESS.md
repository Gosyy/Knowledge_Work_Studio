# P9-5 Provenance usefulness hardening from human review

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `647342bc420192bdf0267ef7ac31344eec786daa`
- Kimi-level claimed: `False`

## Purpose

P9-5 applies the next focused hardening patch from P9-1B human review results. P9-2 addressed fallback planning/content issues, P9-3 addressed renderer layout issues, and P9-4 connected visual QA to semantic/product-quality red flags. P9-5 targets the remaining provenance usability finding: slide coverage was technically complete, but evidence was still only medium-useful for fast human validation.

## Runtime behavior

The local K5 source-to-slide provenance runtime now emits deterministic operator evidence cards in the manifest section. Each card contains:

- slide id and slide index;
- citation id and fragment id;
- bounded slide claim preview;
- bounded evidence excerpt preview;
- match score and usefulness score;
- review priority;
- operator review hint;
- optional locator.

The cards are designed for operator review and artifact audit. They do not require network access, external LLMs, cloud vision, database changes, API endpoints, frontend runtime changes, dependency updates, or Docker/base-image changes.

## Safe metadata

P9-5 adds safe metadata flags and aggregate counts only:

- `p9_5_operator_evidence_review_supported`;
- `operator_evidence_cards_supported`;
- `evidence_review_manifest_section_supported`;
- `human_provenance_usefulness_hardening_supported`;
- `operator_evidence_card_count`;
- `low_usefulness_evidence_card_count`;
- `operator_evidence_review_required`;
- `evidence_usefulness_score_min`;
- `evidence_usefulness_score_average`.

Safe metadata does not store raw source text, raw prompt text, or raw sensitive values. Bounded excerpt previews remain in the manifest evidence section where K5 already stores redacted excerpt previews and digests.

## Scope guard

P9-5 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, hidden public internet runtime requirements, or Kimi-level claims.

## Acceptance

P9-5 is accepted only when:

- `scripts/kw_p9_5_provenance_usefulness_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_5_provenance_usefulness.py` passes;
- previous P9-2, P9-3 and P9-4 checkers remain ready;
- K5/RCH2 checks remain ready;
- production readiness `--checks-only` includes the P9-5 files;
- after commit and push, the full runner and Docker smoke pass.

P9-5 is a targeted provenance-usability hardening patch. It does not claim whole-project Kimi-level parity.
