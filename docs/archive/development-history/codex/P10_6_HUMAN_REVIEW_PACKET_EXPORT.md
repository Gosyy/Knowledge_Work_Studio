# P10-6 — Human review packet export

- status: `controlled_human_review_packet_export`
- branch: `9_Product_Release_Hardening`
- baseline before P10-6: `6ab666e845898731d27e0b109b722c2eace70787`
- Kimi-level claimed: `False`

## Purpose

P10-6 exports a persistent human-review packet from the accepted P10 evidence chain. It exists because P10-5 correctly deferred release approval while the P10-4 worksheets remain pending.

The packet is intended for a real human reviewer. It bundles regenerated post-P9 artifact evidence, comparison data, and review worksheets so the reviewer can inspect the decks and fill a decision for each of the five golden benchmark cases.

## Decision boundary

P10-6 does not complete the review and does not approve the release. It keeps the supported release decision as `defer_pending_human_re_review` and `release_approval_granted_by_p10_6 = false`.

## Evidence included

The exported packet is built from P10-2 regenerated post-P9 golden artifacts, P10-3 comparison cards, P10-4 pending human-review worksheets, P10-5 release decision constraints, and the P10-5a public API GigaChat evidence boundary.

P10-5a is real provider evidence through `public_api_dev`, but it is not production Server 3 offline/intranet proof.

## Operator usage

```bash
python3 scripts/kw_p10_6_human_review_packet_export.py   --repo-root .   --artifacts-dir logs/p10-6-human-review-packet   --export-zip logs/p10-6-human-review-packet.zip   --require-ready   --json
```

The ZIP is generated artifact evidence and should not be committed to the repository.

## Non-goals

P10-6 does not approve or reject any golden deck, change P9-1B or P10 approval state, claim Kimi-level parity, verify production Server 3 offline/intranet GigaChat, repeat the live public API benchmark, remediate npm/dependency warnings, run `npm audit fix --force`, or add API/DB/frontend/dependency/Docker/cloud runtime changes.

## Acceptance

P10-6 is accepted when the checker reports `ready`, a persistent export ZIP can be generated on demand, all five review worksheets remain pending until a human completes them, P10-5 release approval remains deferred, no Kimi-level claim is made, targeted pytest passes, production readiness includes P10-6, the full runner passes with only known non-blocking warnings, and Docker smoke passes on profile 2.\n