# P10-9 — Targeted architecture deck rework and re-review closure

- status: `controlled_targeted_architecture_rework`
- branch: `9_Product_Release_Hardening`
- baseline before P10-9: `8d34eab97eb89920e9f73a19e38b3cad4190c187`
- Kimi-level claimed: `False`

## Purpose

P10-9 resolves the single remaining P10-8 review blocker for `k0_arch_doc_to_architecture_deck` without reopening the whole benchmark phase.

P10-8 preserved the final decision as `defer_pending_targeted_rework` because the completed P10-7 review had four approved cases and one architecture case requiring rework. The blocking finding was a visible title/body layout issue on slide 7 plus repetitive tail slides that did not add architecture-review value.

## Scope

P10-9 is intentionally narrow:

- harden the technical architecture planning path so the 8-slide architecture deck uses a complete architecture-review storyline;
- replace repetitive tail `Opening`/`Context` slides with failure-mode, operator-gate, and release-readiness slides;
- regenerate and inspect only the architecture golden case through the existing RC1/K6 workflow;
- record a targeted re-review closure for this case.

## Non-goals

P10-9 does not grant final release approval, change dependency versions, run `npm audit fix --force`, add API endpoints, add DB migrations, alter Docker base images, add cloud LLM/vision, claim Kimi-level, or verify production Server 3 `local_intranet` GigaChat.

P10-5a public API GigaChat evidence remains real provider evidence for the project completion path, but it is still not Server 3 offline/intranet proof.

## Acceptance

P10-9 is accepted when:

- P10-8 still reports the architecture case as the only blocker before the targeted rework;
- the regenerated architecture artifact passes the RC1/K6 workflow;
- the architecture deck contains the expected 8 architecture-review titles;
- slide 7 is `Failure modes and operator gates` and no longer repeats the opening/context material;
- provenance remains complete and `network_required=false`;
- P10-9 reports `release_decision_supported_after_p10_9 = ready_for_final_release_approval_dossier` while `release_approval_granted_by_p10_9 = false`;
- targeted pytest passes;
- production readiness includes P10-9;
- after commit and push, full runner and Docker smoke pass on the active profile.
