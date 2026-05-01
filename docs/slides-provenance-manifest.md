# S7 — Slides source-to-artifact provenance manifest

S7 links the S3-S6 slides workflow contracts to a concrete provenance manifest
shape for generation and retry artifacts.

## Scope

S7 defines a contract for a downloadable provenance manifest that connects:

- user/session/task identifiers;
- source files and source presentations;
- saved plan snapshots;
- operator instructions as digests, not raw prompts;
- render mode selection and local template policy;
- task event references;
- generated PPTX artifact metadata;
- artifact checksum and manifest digest.

## Non-goals

S7 does not rewrite the PPTX renderer, add a new async runtime, add a browser
dependency, or implement a full slide editor. Runtime persistence of the
manifest may be implemented in a later patch using this contract.

## Manifest rules

Every slides generation manifest must include:

- `manifest_id`
- `schema_version`
- `workflow_id`
- `session_id`
- `task_id`
- `presentation_id`
- `created_at`
- `sources`
- `plan_snapshot`
- `render_attempt`
- `artifact`
- `event_refs`
- `integrity`

Retry manifests must additionally include `retry_links` with parent and newly
created identifiers:

- `parent_task_id`
- `parent_plan_snapshot_id`
- `parent_presentation_version_id`
- `retry_instruction_digest`
- `new_plan_snapshot_id`
- `new_artifact_id`

## Redaction policy

The manifest is safe-payload only. It must not store raw prompts, raw LLM
responses, tokens, API keys, client secrets, database URLs, passwords, or
authorization headers.

## Render mode metadata

Adaptive and template render modes must both record:

- `render_mode`
- `layout_policy`
- `template_source`
- `render_event_id`

Template mode must also record `template_id`.

## Event references

Generation manifests must link the plan-first event chain:

- `slides.plan.approved`
- `slides.render_mode.selected`
- `slides.generation.started`
- `artifact.registered`
- `plan.snapshot.registered`
- `slides.generation.completed`

Retry manifests must link the saved-plan retry event chain:

- `slides.retry.from_saved_plan.requested`
- `slides.retry.saved_plan_snapshot.loaded`
- `slides.retry.plan.validated`
- `slides.retry.render_mode.confirmed`
- `slides.retry.generation.started`
- `artifact.registered`
- `plan.snapshot.registered`
- `slides.retry.generation.completed`

## Operator check

```bash
python scripts/kw_slides_provenance_manifest_check.py --repo-root . --mode generation --require-ready
python scripts/kw_slides_provenance_manifest_check.py --repo-root . --mode retry --json --require-ready
```
