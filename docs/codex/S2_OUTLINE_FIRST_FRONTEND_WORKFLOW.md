# S2 — Outline-first frontend workflow

- status: `controlled_outline_first_frontend_workflow`
- branch: `9_Product_Release_Hardening`
- baseline before S2: `9bade7ea43ef8cc5db994a183d9cdb984e541ebe`
- Kimi-level claimed: `False`

## Purpose

S2 turns the S1 gap item "outline-first workflow" into a controlled frontend-facing workflow contract. The goal is to make the Kimi Slides-derived sequence explicit for KW Studio operators without changing runtime dependencies or claiming Kimi Slides parity.

The required operator journey is:

1. Source intake.
2. Outline draft.
3. Editable outline and plan review.
4. Explicit plan approval.
5. Explicit render mode selection: `adaptive` or `template`.
6. PPTX generation from the approved plan.
7. Artifact history registration.
8. Plan snapshot registration.
9. Retry from saved plan.

Generation must not bypass the approved plan. Retry must use saved plan snapshots rather than hidden transient prompts.

## Frontend contract

S2 is a frontend workflow contract and readiness checkpoint. It does not replace the existing renderer and does not add a full WYSIWYG canvas editor. The frontend-facing requirements are:

- the operator can see an outline before PPTX generation;
- the outline/plan is editable before approval;
- generation is blocked until plan approval is explicit;
- adaptive/template mode selection is visible before generation;
- the generated PPTX is tied to artifact history and a saved plan snapshot;
- retry starts from a saved plan snapshot;
- safe task events are visible/auditable for the plan-first journey.

## Offline and topology boundary

S2 remains offline/intranet compatible. It does not add public API endpoints, DB migrations, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or hidden public-internet production dependencies.

The accepted `public_api_dev` GigaChat benchmark remains release evidence for the completed P10 path, but S2 does not verify Server 3 `local_intranet` and does not represent public API evidence as production offline proof.

## Acceptance

S2 is accepted when the checker reports:

- S1 gap dossier remains ready;
- outline-first frontend workflow is complete as a contract;
- the nine-step frontend journey is present in order;
- direct PPTX generation without plan approval is forbidden;
- adaptive and template render modes are present;
- retry from saved plan is required;
- no Kimi-level claim is made;
- no Server 3 local-intranet proof claim is made;
- production readiness includes the S2 checkpoint.
