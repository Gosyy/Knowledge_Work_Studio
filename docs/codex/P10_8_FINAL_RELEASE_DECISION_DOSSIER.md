# P10-8 — Final release decision dossier after completed human review

- status: `controlled_final_release_decision_dossier`
- branch: `9_Product_Release_Hardening`
- baseline before P10-8: `6bf239d5f5399923a451d93ddd5f305fc3e51f6a`
- Kimi-level claimed: `False`

## Purpose

P10-8 creates the final P10 release decision dossier after P10-7 ingested completed human-review results for the five post-P9 golden benchmark cases.

The dossier is intentionally a decision checkpoint, not an automatic approval mechanism. It summarizes the completed review outcome, records the remaining blocking case, and preserves the GigaChat evidence boundary chosen for this project completion path.

## Human-review outcome used

P10-7 ingested project-owner-accepted AI-assisted review evidence from the P10-6 human-review packet:

- completed review decisions: `5/5`;
- approved cases: `4`;
- request-rework cases: `1`;
- rejected cases: `0`;
- blocking case: `k0_arch_doc_to_architecture_deck`.

Because one golden benchmark case still has `request_rework`, P10-8 must not grant release approval. The supported decision is `defer_pending_targeted_rework` until the architecture-deck issue is fixed or an explicit owner waiver is recorded in a later controlled checkpoint.

## GigaChat boundary

The project completion path may rely on the accepted real GigaChat `public_api_dev` benchmark evidence from P10-5a. P10-8 does not require a production Server 3 `local_intranet` proof and does not claim that Server 3 has been verified.

The target production/offline deployment mode remains local/intranet. Server 3 local-intranet operator readiness should be prepared as a separate non-verification readiness/runbook track if needed, without representing it as proof that the route was exercised.

## Non-goals

P10-8 does not approve the release, auto-approve decks, alter the review results, claim Kimi-level parity, verify the production Server 3 local-intranet route, run the live public API benchmark again, remediate npm/dependency warnings, run `npm audit fix --force`, or add API, DB, frontend, dependency, Docker, cloud LLM, or cloud vision changes.

## Acceptance

P10-8 is accepted when:

- `scripts/kw_p10_8_final_release_decision_dossier.py --repo-root . --require-ready --json` reports `ready`;
- it confirms completed human review results from P10-7;
- it records `4 approve`, `1 request_rework`, `0 reject`;
- it keeps release approval ungranted;
- it preserves the public-API-vs-Server-3 GigaChat boundary;
- targeted pytest passes;
- production readiness `--checks-only` passes and the executable gate includes P10-8;
- after commit and push, full runner and Docker smoke pass on the active profile.
