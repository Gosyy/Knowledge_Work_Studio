# P10-5 — Release decision dossier

- status: `controlled_release_decision_dossier`
- branch: `9_Product_Release_Hardening`
- baseline before P10-5: `157776bc14cb759c4a8b2bd3453d41f6c02dde52`
- Kimi-level claimed: `False`

## Purpose

P10-5 creates the release decision dossier after the post-P9 regeneration, comparison, human re-review capture workflow, and GigaChat API benchmark checkpoint.

This checkpoint is deliberately a decision dossier, not an automatic release approval. The current P10-4 review packet still contains pending human-review worksheets, so P10-5 must preserve the decision as `defer_pending_human_re_review` until a real reviewer completes all five golden-case worksheets.

## Evidence chain

P10-5 references the accepted P10 evidence chain:

- P10-1 regeneration readiness;
- P10-2 post-P9 artifact pack generation;
- P10-3 post-P9 artifact comparison against P9-1B findings;
- P10-4 human re-review capture workflow;
- P10-5a public API GigaChat golden benchmark execution.

P10-5a provides real GigaChat API evidence through the `public_api_dev` route. It does not verify the production Server 3 `local_intranet` route and must not be represented as offline/intranet topology proof.

## Decision

Until the P10-4 worksheets are completed by a human reviewer, the only supported release decision is:

```text
release_decision = defer_pending_human_re_review
release_approval_granted_by_p10_5 = false
```

This is an accepted dossier state, not a product approval state.

## Non-goals

P10-5 does not:

- approve any golden deck automatically;
- reject any golden deck automatically;
- change the original P9-1B review decisions;
- claim Kimi-level parity;
- verify the production Server 3 offline/intranet GigaChat route;
- remediate npm/dependency warnings;
- run `npm audit fix --force`;
- add an API endpoint, DB migration, frontend runtime, dependency change, Docker/base-image change, cloud production LLM, or cloud vision.

## Acceptance

P10-5 is accepted when:

- `scripts/kw_p10_5_release_decision_dossier.py --repo-root . --require-ready --json` reports `ready`;
- the release decision is `defer_pending_human_re_review` while P10-4 worksheets remain pending;
- no Kimi-level claim is made;
- P10-5a public API evidence is explicitly separated from Server 3 offline/intranet proof;
- targeted pytest passes;
- production readiness `--checks-only` includes P10-5;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
