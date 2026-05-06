# P9-7 Golden benchmark post-hardening review readiness

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `0879dfd81b00db67ea20a15cb326c44c17849984`
- Kimi-level claimed: `False`

## Purpose

P9-7 closes the evidence/readiness loop after P9-2 through P9-6. Earlier P9 patches hardened renderer content, renderer layout, visual-QA semantic guards, provenance usefulness, and semantic source coverage. P9-7 does not mark the generated golden benchmark decks as approved and does not claim Kimi-level parity.

Instead, it produces a deterministic post-hardening review-readiness packet so an operator can re-run or re-review the five golden benchmark cases against the original P9-1B findings. The packet maps each original `request_rework` case to the hardening evidence that now exists and keeps the final approval decision reserved for a future human review.

## Human-review findings covered by the packet

The P9-7 readiness packet tracks the original conservative findings and their hardening evidence:

- generic fallback labels and filler slides: P9-2, P9-3, P9-4;
- weak comparison-table treatment: P9-2, P9-3, P9-4;
- project-log late-phase omissions: P9-2, P9-6;
- long structured source filler and late coverage: P9-2, P9-6;
- provenance usefulness: P9-5, P9-6;
- visual QA score versus human review mismatch: P9-4.

## Runtime behavior

P9-7 is evidence-only. It adds a checker and smoke test that read the P9-1B human-review fixture and verify that every golden benchmark case remains explicitly marked for human re-review. The checker emits safe readiness metadata, including case IDs, original decisions, hardening evidence IDs, and conservative follow-up state.

The patch does not regenerate benchmark artifacts, does not approve any deck, and does not alter generation runtime behavior. It only makes the post-hardening review state explicit and verifiable.

## Scope guard

P9-7 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public internet runtime requirements, or Kimi-level claims.

## Acceptance

P9-7 is accepted only when:

- `scripts/kw_p9_7_golden_review_readiness_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_7_golden_review_readiness.py` passes;
- previous P9 checkers remain ready;
- production readiness `--checks-only` includes the P9-7 evidence files;
- after commit and push, the full runner and Docker smoke pass on profile 2.
