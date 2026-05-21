# P10-2 Post-P9 golden artifact pack generation

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `2bc43dad0a55011c8627841b6fd5e2cc7be12f09`
- Kimi-level claimed: `False`

## Purpose

P10-2 is the first generation checkpoint in the post-P9 validation phase. P10-1 proved that the repository is ready to regenerate the five golden benchmark cases after P9 hardening. P10-2 runs the accepted local/offline RC1/K6 harness and produces a post-P9 golden benchmark artifact pack for the same five cases.

P10-2 does not approve any deck, does not change the original P9-1B human review decisions, and does not claim Kimi-level parity. It only produces a verifiable artifact pack that can be compared against the original P9-1B findings in P10-3 and reviewed by a human operator in P10-4.

## Generated artifact pack

The checker runs `scripts/kw_rc1_golden_benchmark_harness.py` with an artifacts directory. For each golden benchmark case it expects the same triplet shape used by the RC1 harness:

- `rc1-<case_id>.pptx`;
- `manifest.json`;
- `safe_metadata.json`.

P10-2 also writes `p10_2_post_p9_artifact_pack_manifest.json` into the artifact directory. The pack manifest records the case IDs, generated paths, checksums, visual QA status, provenance coverage status, and the requirement for human re-review.

When production readiness runs the P10-2 checker, the artifacts are generated in a temporary directory and discarded after verification. When an operator passes `--artifacts-dir`, the artifact pack is persisted for P10-3/P10-4.

## Review boundary

P10-2 preserves the original conservative P9-1B review boundary:

- the five original golden cases remain `request_rework` until a new human review is completed;
- generated post-P9 artifacts are not automatically approved;
- automated proxy scores and visual QA are not treated as human approval;
- Kimi-level parity is not claimed.

## Scope guard

P10-2 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

P10-2 does not run `npm audit fix --force`, does not change package versions, and does not remediate dependency/security warnings. Those remain a separate controlled track. Known npm and RC2 warnings remain the same non-blocking warnings already classified by P9-7/P9-8.

## Acceptance

P10-2 is accepted only when:

- `scripts/kw_p10_2_post_p9_artifact_pack.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p10_2_post_p9_artifact_pack.py` passes;
- P10-1 readiness remains ready;
- production readiness `--checks-only` includes the P10-2 executable step;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
