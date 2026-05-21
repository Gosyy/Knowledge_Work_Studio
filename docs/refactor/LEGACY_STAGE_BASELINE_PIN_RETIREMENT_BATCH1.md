# KR-3C Legacy Stage Baseline Pin Retirement Batch 1

KR-3C executes the first controlled retirement batch for legacy stage baseline pins.

## Purpose

KR-3B classified portability debt into cleanup batches. The largest safe next category is legacy stage baseline pin retirement: old stage checkers can contain raw commit pins and historical release branch checks.

KR-3C does not edit hundreds of legacy scripts in place. It creates a machine-readable retirement manifest and separates legacy stage baseline pins from product portability requirements.

## Execution mode

```text
retirement_manifest_and_reclassification
```

This means:

- selected legacy stage checkers are recorded in a retirement manifest;
- active referenced checkers are not edited or removed in this patch;
- inactive candidates are identified for later archive;
- product-level replacement checks remain the source of truth for new behavior;
- `docs/codex` remains physically in place.

## Why not rewrite every file now

Many stage checkers are still referenced by the production readiness gate or by historical smoke tests. Editing them all at once would be high risk and would make failures hard to debug.

KR-3C keeps the change narrow:

```text
identify batch 1;
record safe action for each selected legacy checker;
verify product replacement checks still pass;
leave runtime behavior unchanged.
```

## Batch 1 action types

```text
eligible_for_archive_after_product_replacement_verification
reclassify_as_legacy_safety_net_before_editing
```

The first action is for inactive legacy stage checkers. The second action is for active referenced checkers that cannot be safely edited until they are removed from active gates.

## Non-goals

KR-3C does not:

- delete legacy scripts;
- edit active stage checkers in place;
- remove smoke tests;
- move `docs/codex`;
- reduce product quality gates;
- claim that all portability debt is fixed.

## Acceptance criteria

```text
KR-3C retirement manifest reports ready;
batch 1 selects at least one legacy stage baseline pin group;
active referenced checkers are reclassified, not edited;
KR-3A path portability policy remains ready;
KR-3B cleanup plan remains ready;
post-audit is generated;
post-test-map is generated;
post-stage-dependency inventory is generated;
product replacement checks remain ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
