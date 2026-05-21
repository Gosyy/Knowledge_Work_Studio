# S6 Slides adaptive/template render mode contract

S6 hardens the render-mode decision layer for plan-first slides workflows.
It deliberately avoids a PPTX renderer rewrite, a full slide editor, a new async
runtime, or any browser/internet dependency.

## Product rule

Slides generation must use an approved saved plan snapshot and an explicit render
mode decision.

Supported render modes:

- `adaptive`: KW Studio may choose local layouts from the approved plan and bundled
  template library.
- `template`: KW Studio must use an explicit local `template_id`; it must not
  silently fall back to adaptive layout selection.

## Required metadata

Every render attempt must be able to register safe artifact/task metadata:

- `render_mode`
- `plan_snapshot_id`
- `layout_policy`
- `template_source`
- `template_id` for template mode

## Required safe events

- `slides.plan.approved`
- `slides.render_mode.selected`
- `slides.render_mode.validated`
- `slides.render_mode.applied`
- `slides.generation.started`
- `artifact.registered`
- `plan.snapshot.registered`
- `slides.generation.completed`

## Offline constraints

S6 is offline-ready. Template mode references local templates only. External
template downloads are explicitly disallowed.

## Non-goals

- No PPTX renderer rewrite.
- No full slide editor.
- No new async runtime.
- No browser or internet dependency.
