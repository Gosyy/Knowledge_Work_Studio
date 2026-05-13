# KW Studio RF2.2 Minimal Deterministic PPTX Generation from Approved Plan

## Status

RF2.2 checkpoint: minimal deterministic PPTX generation from an approved plan.

This checkpoint adds a narrow runtime bridge:

approved `PresentationPlan` → deterministic PPTX bytes → safe render metadata.

RF2.2 is the first RF2 step that adds an additive backend runtime path for slides generation from an approved plan. It still does not claim Kimi-level slides quality and does not complete the full Kimi-level product loop.

## Why this exists

RF2.1 proved that a baseline deterministic PPTX generator exists, but also correctly recorded that the whole product loop is not Kimi-level.

RF2.2 turns that baseline into a deliberately narrow runtime capability:

- the plan must already be approved;
- the plan must already be a structured `PresentationPlan`;
- the renderer is deterministic and local;
- the result includes checksum, size, slide count, render mode, template id, and safe event hints;
- no internet, cloud model, dependency upgrade, Docker change, browser runtime, or frontend runtime change is introduced.

## What RF2.2 adds

RF2.2 adds:

- `backend/app/services/slides_service/approved_plan.py`;
- `ApprovedPlanRenderRequest`;
- `ApprovedPlanRenderResult`;
- `render_approved_plan_to_pptx`;
- `SlidesService.generate_deck_from_approved_plan`;
- `scripts/kw_slides_approved_plan_runtime_check.py`;
- smoke tests for deterministic approved-plan rendering.

## Runtime contract

The approved-plan runtime path must:

1. reject plans that are not explicitly approved;
2. reject empty plans;
3. reject unsupported render modes;
4. require `template_id` when render mode is `template`;
5. render using existing local `generate_pptx_from_plan`;
6. return deterministic bytes for identical inputs;
7. compute `sha256`;
8. return `size_bytes`;
9. return `slide_count`;
10. return `artifact_filename`;
11. return `content_type`;
12. return safe task event names;
13. avoid raw prompt, raw LLM response, credentials, or secrets in metadata.

## What RF2.2 does not do

RF2.2 does not:

- introduce an API endpoint yet;
- persist the generated PPTX artifact yet;
- persist task events yet;
- emit the downloadable provenance manifest yet;
- implement saved-plan retry yet;
- implement visual QA runtime;
- implement browser evidence runtime;
- implement local GigaChat planning;
- improve renderer layout quality to Kimi-level;
- change dependency versions;
- change Dockerfiles;
- run `npm audit fix`;
- run `npm audit fix --force`.

## Kimi-level interpretation

RF2.2 is a required step toward Kimi-level, but it does not reach Kimi-level.

A Kimi-level slides product requires the whole loop to mature:

source intake → document understanding → local/offline planning → editable plan → approved-plan generation → renderer/layout quality → artifact history → provenance → visual QA → retry lifecycle → operator-visible event stream → reproducible offline deployment.

RF2.2 only closes this part:

approved plan → deterministic PPTX bytes + safe metadata.

## Acceptance

RF2.2 is accepted when:

- approved-plan runtime module exists;
- `SlidesService.generate_deck_from_approved_plan` exists;
- checker reports `approved_plan_runtime_supported: true`;
- checker reports `kimi_grade_supported: false`;
- checker reports `whole_project_kimi_level_supported: false`;
- deterministic byte/hash smoke passes;
- rejection of unapproved plan is tested;
- template mode requires explicit local template id;
- production readiness includes the RF2.2 check;
- full post-RF2.2 runner passes;
- Docker runtime smoke with `--skip-build` passes;
- remote `7_Runtime_Foundation` matches the local RF2.2 verdict commit;
- working tree is clean after cleanup.

## Next

After RF2.2:

RF2.3 — Plan snapshot persistence and task event stream runtime wiring.

RF2.3 should take RF2.2 output and connect it to stored plan snapshots and event lifecycle without claiming Kimi-level quality prematurely.
