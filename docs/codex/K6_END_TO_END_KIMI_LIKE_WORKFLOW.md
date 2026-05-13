# K6 — End-to-end Kimi-like workflow

Status: controlled K-phase runtime patch.

K6 composes the previously accepted K0-K5 building blocks into one local,
operator-gated workflow:

1. K1 local GigaChat-first planning with deterministic fallback.
2. K2 editable plan editor session and explicit approval gate.
3. K3 deterministic renderer-quality pass.
4. K5 source-to-slide provenance and bounded evidence manifest section.
5. Approved-plan PPTX rendering.
6. K4 deterministic OOXML visual QA.
7. Final operator gate before delivery.

K6 is deliberately a workflow/runtime layer, not a product-wide claim that KW
Studio has already reached full Kimi-level capability. The checker validates a
Kimi-like path through the local workflow gates while preserving the controlled
K-phase boundary.

## Guarantees

- Source-to-PPTX workflow is supported locally.
- Downloadable PPTX artifact metadata is produced.
- K1-K5 runtime checkpoints are integrated into a single safe result model.
- K5 slide-level evidence coverage must be complete.
- K4 visual QA must be deliverable and operator-approved.
- Safe manifest metadata is emitted without raw source text or raw prompts.
- Default path remains offline/intranet safe.
- Direct local GigaChat remains the first-class provider path; deterministic
  fallback remains available when local GigaChat is not configured.

## Explicit non-goals

K6 does not add:

- a public API endpoint;
- a DB schema migration;
- a frontend runtime rewrite;
- dependency version changes;
- Dockerfile or base image changes;
- cloud LLM or cloud vision;
- hidden public internet use;
- a whole-product Kimi-level claim.

## Runtime surface

Primary module:

- `backend/app/services/k_phase/end_to_end_workflow.py`

Primary checker:

- `scripts/kw_k6_end_to_end_workflow_check.py`

Primary smoke test:

- `backend/tests/smoke/test_k6_end_to_end_workflow.py`

## Acceptance condition

K6 is accepted only after:

- targeted K6 runner PASS;
- functional commit;
- empty verdict commit;
- push to `8_K_Phase`;
- full runner PASS;
- Docker smoke PASS.

After K6 passes, KW Studio has a controlled end-to-end Kimi-like workflow path
for the K-phase benchmark scenarios. This still must not be worded as an
unqualified claim that the whole product is already Kimi-level.
