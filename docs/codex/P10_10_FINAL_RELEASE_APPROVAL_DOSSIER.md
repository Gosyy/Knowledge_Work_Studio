# P10-10 — Final release approval dossier

- status: `controlled_final_release_approval_dossier`
- branch: `9_Product_Release_Hardening`
- baseline before P10-10: `405a6ea1a418ec1aa5df5648ce0dcba1da2e073d`
- Kimi-level claimed: `False`

## Purpose

P10-10 creates the final release approval dossier after P10-9 resolved the only remaining P10-8 human-review blocker. It is the first P10 checkpoint that can grant release approval, because all five golden benchmark cases are approved after targeted architecture rework.

## Approval basis

The dossier relies on the accepted P10 chain:

- P10-1 through P10-6 prepared, regenerated, compared, and exported post-P9 golden review evidence;
- P10-7a validated completed review payloads;
- P10-7 ingested the owner-accepted AI-assisted human review results;
- P10-8 correctly deferred approval because the architecture deck still requested rework;
- P10-9 resolved the architecture request-rework case and left zero blocking golden benchmark cases.

P10-10 records `final_release_decision_by_p10_10 = approved_for_release` and `release_approval_granted_by_p10_10 = true` only when P10-9 reports five approved cases, zero request-rework decisions, zero rejects, and no blocking case IDs.

## Boundary conditions

P10-10 does not claim Kimi-level parity and does not verify the production Server 3 `local_intranet` GigaChat route. The accepted P10-5a GigaChat benchmark remains real provider evidence through `public_api_dev`, not Server 3 offline/intranet proof.

The production/offline mode remains the target deployment mode. Server 3 local-intranet operator readiness can be prepared separately without claiming verification in P10-10.

Known npm audit/deprecated warnings remain inherited non-blocking warnings for this release path. Dependency/security remediation remains a separate controlled track; P10-10 does not run `npm audit fix --force`.

## Non-goals

P10-10 does not add API endpoints, DB migrations, dependency changes, Docker/base-image changes, frontend runtime changes, cloud LLM, cloud vision, or hidden public-internet production dependencies.

## Acceptance

P10-10 is accepted when:

- `scripts/kw_p10_10_final_release_approval_dossier.py --repo-root . --require-ready --json` reports `ready`;
- the dossier grants release approval only after P10-9 reports all five golden cases approved;
- no owner waiver is used;
- no Kimi-level claim is made;
- Server 3 `local_intranet` remains not verified by this checkpoint;
- targeted pytest passes;
- production readiness includes P10-10;
- after commit and push, full runner and Docker smoke pass on the active profile.
