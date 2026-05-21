# P9-8 Product release hardening closure dossier

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `c1f6735a21fa82d13e2638d7b20ee304911275ab`
- Kimi-level claimed: `False`

## Purpose

P9-8 closes the P9 product-release hardening track as an evidence-only closure dossier. P9-1 captured conservative human review results, P9-2 through P9-6 applied focused hardening from those findings, and P9-7 produced a post-hardening golden-review readiness packet with explicit known-warning classification.

P9-8 does not mark any generated golden deck as approved and does not claim Kimi-level parity. It records that the P9 hardening evidence is complete enough to hand back to an operator for regeneration and human re-review, while preserving the original conservative approval state until a new review is performed.

## Closure evidence chain

P9-8 requires the following evidence chain to be present and checkable:

- P9-1 golden benchmark human review results: five completed `request_rework` cases and no Kimi-level claim;
- P9-2 renderer/content hardening: fallback labels, comparison-table planning, project-log coverage, and filler-slide prevention;
- P9-3 renderer layout hardening: case-appropriate comparison/data layouts and removal of arbitrary renderer labels;
- P9-4 visual QA semantic guard: product-quality red flags can affect visual QA status even when OOXML layout checks are clean;
- P9-5 provenance usefulness: operator evidence cards make citations easier to review;
- P9-6 semantic source coverage: late-source signals and closure/risk/next-action sections are tracked explicitly;
- P9-7 post-hardening review readiness and warning classification: every original case remains queued for human re-review, and full-runner warnings are known non-blocking warnings for this evidence track.

## Known non-blocking warnings

P9-8 inherits the P9-7 warning classification:

- deprecated transitive npm packages are known non-blocking warnings for this P9 evidence patch;
- npm audit vulnerability summaries are not remediated here and remain a separate controlled dependency/security track;
- RC2 `warning_findings` are conservative golden-review evidence, not release-gate failures;
- no `npm audit fix --force` is run by P9-8;
- dependency versions and lockfiles are not changed by P9-8.

## Runtime behavior

P9-8 is evidence-only. It adds a closure checker and smoke test, and extends the production readiness gate so the closure dossier becomes part of the release-hardening evidence set.

It does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

## Closure verdict

P9-8 can be accepted when:

- `scripts/kw_p9_8_product_release_hardening_closure_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_8_product_release_hardening_closure.py` passes;
- P9-2 through P9-7 checkers remain ready;
- production readiness `--checks-only` includes the P9-8 closure files;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
