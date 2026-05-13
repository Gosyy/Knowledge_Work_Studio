# KW Studio RF2.3 Approved Plan Lifecycle Runtime

## Status

RF2.3 checkpoint: plan snapshot persistence and task event stream runtime wiring.

This checkpoint connects RF2.2 approved-plan rendering to the existing plan snapshot service and the S4 slides task event contract.

RF2.3 adds runtime lifecycle wiring, not Kimi-level slides quality.

## Runtime path

RF2.3 adds this narrow runtime path:

approved `PresentationPlan`
-> deterministic PPTX render
-> artifact registration through the existing artifact service
-> plan snapshot persistence through `PresentationPlanSnapshotService`
-> append-only safe task event stream
-> lifecycle result with safe metadata.

## What RF2.3 adds

RF2.3 adds:

- `backend/app/services/slides_service/approved_plan_lifecycle.py`;
- `ApprovedPlanLifecycleRequest`;
- `ApprovedPlanLifecycleResult`;
- `SlidesTaskEvent`;
- `render_approved_plan_with_lifecycle`;
- `SlidesService.generate_deck_from_approved_plan_with_lifecycle`;
- official composition wiring for `plan_snapshot_service` and `artifact_service`;
- `scripts/kw_slides_approved_plan_lifecycle_check.py`;
- smoke tests for deterministic approved-plan rendering, persisted plan snapshot, artifact registration, event order, and safe payload.

## Existing foundation reused

RF2.3 intentionally reuses:

- RF2.2 `render_approved_plan_to_pptx`;
- existing `PresentationPlanSnapshotService`;
- existing artifact service `create_artifact_from_bytes`;
- existing S4 slides task event contract.

## Event stream

The RF2.3 runtime emits an in-memory append-only event tuple for the generation lifecycle:

1. `slides.plan.approved`
2. `slides.render_mode.selected`
3. `slides.generation.started`
4. `artifact.registered`
5. `plan.snapshot.registered`
6. `slides.generation.completed`

Each event contains only safe payload fields allowed by the S4 contract.

## Safe payload policy

Event safe payload must only use:

- `plan_snapshot_id`;
- `presentation_id`;
- `presentation_version_id`;
- `render_mode`;
- `artifact_id`;
- `artifact_filename`;
- `retry_of_task_id`;
- `change_summary`;
- `error_code`.

RF2.3 must not place raw prompts, raw LLM responses, credentials, secrets, database URLs, authorization headers, raw file bytes, or raw screenshots into events.

## What RF2.3 does not do

RF2.3 does not:

- add a new public API endpoint;
- add a DB schema migration;
- implement saved-plan retry;
- emit the downloadable provenance manifest;
- implement visual QA runtime;
- implement local GigaChat planning;
- improve renderer quality to Kimi-level;
- change dependencies;
- change Dockerfiles;
- run `npm audit fix`;
- run `npm audit fix --force`.

## Kimi-level interpretation

RF2.3 is required infrastructure for Kimi-level, but it does not reach Kimi-level.

Kimi-level remains deferred to K-phase after RF closure and means the whole slides product loop, not just generator output.

## Acceptance

RF2.3 is accepted when:

- lifecycle runtime module exists;
- `SlidesService.generate_deck_from_approved_plan_with_lifecycle` exists;
- official composition passes `plan_snapshot_service` and `artifact_service` into `SlidesService`;
- checker reports `approved_plan_lifecycle_supported: true`;
- checker reports `plan_snapshot_persisted: true`;
- checker reports `artifact_registered: true`;
- checker reports `event_order_valid: true`;
- checker reports `safe_payload_only: true`;
- checker reports `kimi_grade_supported: false`;
- targeted smoke tests pass;
- production readiness includes RF2.3;
- full runner passes after commit;
- Docker runtime smoke with `--skip-build` passes after commit.

## Next

RF2.4 — Saved-plan retry runtime path.
