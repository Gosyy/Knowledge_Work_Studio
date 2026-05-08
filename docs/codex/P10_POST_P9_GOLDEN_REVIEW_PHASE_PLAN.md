# P10 Post-P9 golden benchmark regeneration and human re-review plan

- status: `controlled_phase_start`
- branch: `9_Product_Release_Hardening`
- baseline before phase: `42d999a93a6328c1f35e8e3118b6bca6ab3f45ca`
- Kimi-level claimed: `False`

## Purpose

P10 starts after the closed P9 product-release hardening evidence track. P9 captured human-review findings, applied focused content/layout/visual-QA/provenance/semantic-coverage hardening, produced review-readiness evidence, and closed with known non-blocking warning classification.

P10 is the validation phase that checks whether the P9 hardening actually improved the golden benchmark artifacts for a human reviewer. It must regenerate or re-open post-P9 artifacts, compare them against the original P9-1B findings, and perform a new human re-review before changing any approval state.

## P10-1 - Post-P9 regeneration readiness

P10-1 is intentionally evidence-only. It does not regenerate PPTX artifacts by itself. It verifies that the repository contains the accepted P9 closure chain, the original five P9-1B `request_rework` golden cases, and the RC1 golden benchmark harness needed to produce a post-P9 artifact pack.

The output of P10-1 is a deterministic regeneration plan:

- five golden benchmark case IDs to regenerate;
- expected artifact triplets per case: PPTX, manifest, safe metadata;
- preserved original P9-1B decisions, all still `request_rework` until re-review;
- explicit requirement for future human re-review;
- known non-blocking warning classification inherited from P9-7/P9-8;
- no Kimi-level claim.

## Next P10 steps

The intended follow-up sequence is:

1. `P10-2` - generate a post-P9 golden benchmark artifact pack using the accepted local/offline harness.
2. `P10-3` - compare the post-P9 artifacts against the original P9-1B findings.
3. `P10-4` - run or capture a new human re-review using the existing rubric.
4. `P10-5` - create a release decision dossier from the new review results.
5. Targeted fixes only if the new human review still finds blockers.


## P10-2 - Post-P9 golden artifact pack generation

P10-2 starts from accepted P10-1 on branch `9_Product_Release_Hardening` at `2bc43dad0a55011c8627841b6fd5e2cc7be12f09`. It runs the accepted local/offline RC1/K6 golden benchmark harness to generate a post-P9 artifact pack for the same five golden cases.

The patch verifies one PPTX, one manifest, and one safe metadata file per case, plus a P10-2 artifact pack manifest. It does not approve any deck, does not change the original P9-1B review decisions, and does not claim Kimi-level parity. Human re-review remains required before any approval-state change.

P10-2 is registered in the production readiness executable gate as an artifact-pack generation checkpoint. The production gate uses a temporary artifact directory, while operators can pass `--artifacts-dir` to persist the pack for P10-3/P10-4.

## Scope guard

P10-1 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

P10-1 does not run `npm audit fix --force`, does not change package versions, and does not remediate dependency/security warnings. Those remain a separate controlled track.

## Acceptance

P10-1 is accepted only when:

- `scripts/kw_p10_1_post_p9_regeneration_readiness_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py` passes;
- P9-8 closure evidence remains present;
- production readiness `--checks-only` includes the P10-1 files;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.

## Production readiness gate integration

P10-1 is registered in the production readiness executable gate as an evidence-only checkpoint. The gate runs `scripts/kw_p10_1_post_p9_regeneration_readiness_check.py --require-ready --json` after the P9 closure checks so the start of the post-P9 regeneration phase is visible in full-runner logs rather than only in targeted runner logs.

This integration does not generate artifacts, does not change approval state, does not run `npm audit fix --force`, does not change dependency versions, and does not claim Kimi-level parity.
