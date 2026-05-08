# P10-3 Post-P9 artifact comparison report

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `969ebc040a1ab6d30425141d26a1e39f558a8d8d`
- Kimi-level claimed: `False`

## Purpose

P10-3 compares regenerated post-P9 golden benchmark artifacts against the original P9-1B human-review findings. P10-2 proves that the post-P9 artifact pack can be generated; P10-3 turns that pack into a deterministic comparison report for the next human re-review step.

The comparison report preserves the original conservative P9-1B state. It does not mark any deck as approved, does not change any review decision, and does not claim Kimi-level parity.

## What P10-3 checks

P10-3 runs the P10-2 artifact-pack generator in an isolated artifact directory, then builds one comparison card per golden benchmark case. Each card records original P9-1B findings, regenerated artifact evidence, manifest/safe-metadata digests, and a human re-review instruction.

## Operator boundary

P10-3 is not the re-review itself. It prepares evidence for P10-4. A future operator must open the post-P9 artifacts and compare them against these cards and the original P9-1B findings before recording any new decision.

## Scope guard

P10-3 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

P10-3 does not run `npm audit fix --force`, does not change package versions, and does not remediate dependency/security warnings. Those remain a separate controlled track.

## Acceptance

P10-3 is accepted only when:

- `scripts/kw_p10_3_post_p9_artifact_comparison.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p10_3_post_p9_artifact_comparison.py` passes;
- P10-2 and P10-1 checks remain ready;
- production readiness `--checks-only` includes the P10-3 comparison step;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
