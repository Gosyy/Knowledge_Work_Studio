# P10-4 Post-P9 human re-review capture workflow

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `c854830ae885ffdde80da6a3de6c0f7466433bd2`
- Kimi-level claimed: `False`

## Purpose

P10-4 creates the deterministic capture workflow for a new post-P9 human re-review. P10-2 regenerates the artifact pack and P10-3 compares the regenerated artifacts against the original P9-1B findings; P10-4 turns that comparison evidence into a human-review packet.

P10-4 does not complete the human review. It does not mark any generated deck as approved, rejected, or reworked. Every worksheet remains `pending_human_review` until an operator opens the regenerated artifact triplet and fills the required rubric fields.

## Review packet

The P10-4 packet contains one worksheet per golden benchmark case:

- original P9-1B decision, which remains `request_rework`;
- allowed future decisions: `approve`, `request_rework`, `reject`;
- required fields: reviewer ID, review timestamp, decision, scores, slide-level findings, and follow-up backlog;
- digest of the P10-3 comparison card;
- original blocker/warning counts and regenerated artifact evidence;
- explicit instruction that the approval state must not change until human review is complete.

## Scope guard

P10-4 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

P10-4 does not run `npm audit fix --force`, does not change dependency versions, and does not remediate dependency/security warnings. Those remain a separate controlled track.

## Acceptance

P10-4 is accepted only when:

- `scripts/kw_p10_4_post_p9_human_re_review.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p10_4_post_p9_human_re_review.py` passes;
- P10-3 comparison and P10-2 artifact generation remain ready;
- production readiness `--checks-only` includes the P10-4 executable step;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
