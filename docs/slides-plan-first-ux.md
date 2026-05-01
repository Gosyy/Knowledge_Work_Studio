# Slides plan-first UX contract (S3)

S3 hardens the KW Studio slides workflow around a product rule inspired by Kimi-style deck generation: the operator must see and be able to work from an outline/plan before deck generation or retry. This is a contract and safety layer, not a new slide editor or renderer.

## Scope

S3 is intentionally narrow.

In scope:

- outline-first deck planning;
- editable plan review before generation;
- explicit render mode selection: adaptive or template;
- retry from a saved plan snapshot;
- safe task events around the plan-first journey;
- offline-compatible validation and diagnostics.

Out of scope:

- replacing the PPTX renderer;
- building a full WYSIWYG slide editor;
- adding internet-dependent template discovery;
- adding autonomous browser generation;
- changing the default GigaChat production LLM topology from S1.

## Required UX sequence

The slides UX must preserve this order:

1. Source intake.
2. Outline draft.
3. Editable plan review.
4. Render mode selection.
5. Generation from the approved plan.
6. Artifact history registration.
7. Plan snapshot registration.
8. Retry from saved plan.

Generation must not bypass the approved plan. Revision and retry flows must prefer saved plan snapshots rather than relying on hidden transient prompts.

## Render modes

S3 defines two product modes:

- `adaptive`: KW Studio can choose layout from the approved plan.
- `template`: KW Studio must constrain rendering to the selected template.

Both modes are offline-compatible. Template mode must use local templates only.

## Safe task events

The minimum safe task event trail is:

- `slides.plan.requested`
- `slides.outline.created`
- `slides.plan.ready_for_review`
- `slides.plan.approved`
- `slides.render_mode.selected`
- `slides.generation.started`
- `artifact.registered`
- `plan.snapshot.registered`
- `slides.retry.from_saved_plan.requested`
- `slides.generation.completed`

These events are the contract for later S-phase work on task event streaming and recovery. S3 does not implement a new queue or event store.

## Acceptance checks

Run:

```bash
python scripts/kw_slides_plan_first_check.py --repo-root . --require-ready
python scripts/kw_slides_plan_first_check.py --repo-root . --mode adaptive --json --require-ready
python scripts/kw_slides_plan_first_check.py --repo-root . --mode template --json --require-ready
python -m pytest backend/tests/smoke/test_s3_slides_plan_first_contract.py -q
```
