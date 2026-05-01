# S4 — Slides task event stream and saved-plan retry mechanics

S4 hardens the S3 plan-first slides workflow by defining the task event stream and retry-from-saved-plan contract.

## Goal

S3 established the product rule: create or revise slides through an editable plan before generation. S4 defines the safe event mechanics around that rule:

1. append-only task events;
2. safe payloads only;
3. saved-plan retry must load an existing plan snapshot;
4. retry must validate the saved plan before generation;
5. retry must confirm render mode;
6. retry must register a new artifact and link provenance.

## Required event schema

Every slides task event must carry:

- `event_id`
- `task_id`
- `session_id`
- `workflow_id`
- `event_type`
- `created_at`
- `safe_payload`

Payloads must be safe summaries and stable identifiers only. Raw credentials, provider keys, database connection strings, and authorization material must be redacted.

## Plan-first event order

The normal plan-first path is:

1. `slides.plan.requested`
2. `slides.outline.created`
3. `slides.plan.ready_for_review`
4. `slides.plan.approved`
5. `slides.render_mode.selected`
6. `slides.generation.started`
7. `artifact.registered`
8. `plan.snapshot.registered`
9. `slides.generation.completed`

Generation must not start before plan approval and render mode selection.

## Retry from saved plan

Retry is not a blind rerun. It is a controlled recovery path:

1. `slides.retry.from_saved_plan.requested`
2. `slides.retry.saved_plan_snapshot.loaded`
3. `slides.retry.plan.validated`
4. `slides.retry.render_mode.confirmed`
5. `slides.retry.generation.started`
6. `artifact.registered`
7. `plan.snapshot.registered`
8. `slides.retry.generation.completed`

Retry must preserve the parent plan snapshot link and must create a new artifact/history entry.

## Offline posture

S4 is offline-ready. It introduces no browser dependency, no internet dependency, no queue broker, and no external event store.

## Non-goals

S4 intentionally does not add:

- a new async worker runtime;
- a queue broker;
- a database event store migration;
- a new PPTX renderer;
- a browser or internet dependency.

Those can be built in later S-phase patches after this contract is accepted.
