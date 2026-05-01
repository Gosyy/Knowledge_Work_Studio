# S5 Slides Plan Editor UI

S5 adds the first user-visible plan-first slides editing surface. It turns the S3/S4 contracts into a small, auditable UI loop without changing the PPTX renderer or adding a new runtime.

## Product intent

The operator should be able to:

1. load the current saved plan snapshot for a presentation;
2. edit the deck title and outline slide fields before generation;
3. explicitly choose adaptive or template render mode;
4. save an editable plan draft;
5. prepare a retry from saved plan request with safe task events and provenance-friendly metadata.

This keeps the Kimi-derived pattern intact: outline first, editable plan review, selected render mode, then generation/retry.

## S5 boundaries

S5 is intentionally narrow.

- It does not replace the PPTX renderer.
- It does not introduce a new async runtime.
- It does not introduce browser or internet dependency.
- It does not build a full slide canvas editor.
- It does not silently mutate historical plan snapshots.

The UI prepares a safe retry request from the saved editable draft. Backend execution can later consume this contract without changing the operator-facing plan-first flow.

## Safety controls

- The UI uses a dedicated `Plan editor presentation id` field, avoiding collisions with existing session and artifact inputs.
- Retry requires a saved editable plan draft and a non-trivial retry instruction.
- The retry preview includes safe task events such as `slides.retry.from_saved_plan.requested`.
- Adaptive/template mode selection is explicit and visible.
- The workflow stays offline-ready and does not require browser automation.

## Acceptance

S5 is accepted only when:

- `kw_slides_plan_editor_check.py --require-ready` passes;
- the S5 smoke test passes;
- frontend E2E includes the plan editor smoke;
- the production readiness gate passes.
