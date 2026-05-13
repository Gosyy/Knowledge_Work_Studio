# KW Studio RF2.4 Saved-Plan Retry Runtime Path

## Status

RF2.4 checkpoint: saved-plan retry runtime path.

This checkpoint turns the RF2.3 lifecycle foundation into a retry-capable runtime path by loading a saved plan snapshot, validating the retry context, regenerating a deterministic PPTX, registering a new artifact, persisting a new plan snapshot, and emitting the retry event sequence.

RF2.4 is still Runtime Foundation work. It does not claim Kimi-level slides quality.

## Runtime path

RF2.4 adds this narrow runtime path:

saved `PresentationPlanSnapshot`
-> deserialize saved `PresentationPlan`
-> validate explicit operator retry instruction
-> confirm render mode
-> deterministic PPTX render
-> artifact registration through the existing artifact service
-> new plan snapshot persistence through `PresentationPlanSnapshotService`
-> append-only safe retry task event stream
-> retry lifecycle result with parent links and safe metadata.

## What RF2.4 adds

RF2.4 adds:

- `backend/app/services/slides_service/saved_plan_retry.py`;
- `SavedPlanRetryRequest`;
- `SavedPlanRetryResult`;
- `retry_saved_plan_with_lifecycle`;
- `SlidesService.retry_deck_from_saved_plan`;
- `scripts/kw_slides_saved_plan_retry_check.py`;
- smoke tests for saved snapshot loading, explicit operator instruction, render mode confirmation, new artifact registration, new plan snapshot persistence, parent links, retry event order, and safe payload.

## Existing foundation reused

RF2.4 intentionally reuses:

- RF2.2 deterministic approved-plan renderer;
- RF2.3 artifact/snapshot/event lifecycle shape;
- existing `PresentationPlanSnapshotService`;
- existing artifact service `create_artifact_from_bytes`;
- existing S4 retry event sequence contract.

## Retry event stream

The RF2.4 runtime emits the S4 retry sequence:

1. `slides.retry.from_saved_plan.requested`
2. `slides.retry.saved_plan_snapshot.loaded`
3. `slides.retry.plan.validated`
4. `slides.retry.render_mode.confirmed`
5. `slides.retry.generation.started`
6. `artifact.registered`
7. `plan.snapshot.registered`
8. `slides.retry.generation.completed`

Each event contains only safe payload fields allowed by the S4 contract.

## Safe metadata policy

RF2.4 stores parent links and the operator instruction digest, not raw operator instruction text:

- `parent_task_id`;
- `parent_plan_snapshot_id`;
- `parent_presentation_version_id`;
- `new_plan_snapshot_id`;
- `new_artifact_id`;
- `retry_instruction_digest`.

RF2.4 must not place raw prompts, raw LLM responses, credentials, secrets, database URLs, authorization headers, raw file bytes, raw screenshots, or raw operator instruction text into events.

## What RF2.4 does not do

RF2.4 does not:

- add a new public API endpoint;
- add a DB schema migration;
- add a queue/event-store migration;
- emit the downloadable provenance manifest;
- implement visual QA runtime;
- implement local GigaChat planning;
- improve renderer quality to Kimi-level;
- change dependencies;
- change Dockerfiles;
- run `npm audit fix`;
- run `npm audit fix --force`.

## Kimi-level interpretation

RF2.4 is required infrastructure for Kimi-level retry UX, but it does not reach Kimi-level.

Kimi-level remains deferred to K-phase after RF closure and means the whole slides product loop, not just generator or retry output.

## Acceptance

RF2.4 is accepted when:

- saved-plan retry runtime module exists;
- `SlidesService.retry_deck_from_saved_plan` exists;
- checker reports `saved_plan_retry_supported: true`;
- checker reports `saved_plan_snapshot_loaded: true`;
- checker reports `new_plan_snapshot_persisted: true`;
- checker reports `new_artifact_registered: true`;
- checker reports `retry_event_order_valid: true`;
- checker reports `retry_parent_links_present: true`;
- checker reports `safe_payload_only: true`;
- checker reports `raw_operator_instruction_stored: false`;
- checker reports `kimi_grade_supported: false`;
- targeted smoke tests pass;
- production readiness includes RF2.4;
- full runner passes after commit;
- Docker runtime smoke with `--skip-build` passes after commit.

## Next

RF2.5 — Adaptive/template local render mode runtime hardening.
