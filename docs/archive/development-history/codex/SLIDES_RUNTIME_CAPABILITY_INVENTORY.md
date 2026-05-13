# KW Studio RF2.1 Slides Runtime Capability Inventory and Baseline Smoke

## Status

RF2.1 checkpoint: slides runtime capability inventory and baseline smoke.

This checkpoint inventories the existing slides runtime and proves only the current deterministic baseline with a no-network smoke check. It does not claim Kimi-grade slides quality, does not claim product-grade deck generation, and does not prove final RF2 slides runtime completeness.

RF2.1 does not change renderer behavior, service behavior, API behavior, persistence behavior, dependency versions, Dockerfiles, LLM topology, browser runtime, or frontend behavior.

## Critical interpretation rule

The presence of `generator.py`, `SlidesService.generate_deck`, or a valid PPTX payload is not enough to claim that KW Studio works at the level of Kimi slides.

RF2.1 must distinguish:

- baseline deterministic PPTX runtime exists;
- product-grade approved-plan generation is still partial;
- Kimi-like product quality is not proven;
- real user-facing slides workflow still requires RF2.2+ runtime work.

## Whole-project Kimi-level rule

Kimi-level target applies to the whole slides product loop, not only to the PPTX generator.

The future target must cover:

1. source intake and document understanding;
2. local/offline GigaChat-backed planning;
3. outline-first plan quality;
4. editable plan UX;
5. template/adaptive render mode selection;
6. slide layout and visual hierarchy quality;
7. generated media and chart/table rendering;
8. downloadable artifact registration;
9. plan snapshot and retry lifecycle;
10. source-to-artifact provenance;
11. visual QA and artifact integrity checks;
12. operator-visible task event stream;
13. offline bootstrap and reproducible deployment gates.

RF2.1 does not prove this whole-project Kimi-level target. It only proves that a baseline deterministic slides runtime exists and identifies the gaps that RF2.2+ must close.

## Why this exists

RF2.0 created the slides runtime phase checkpoint. RF2.1 establishes what the repository already supports before RF2.2 starts narrowing into deterministic PPTX generation from an approved plan.

RF2.1 is intentionally inventory-first:

- identify what is already baseline-runtime-ready;
- identify what is partial runtime;
- identify what remains contract-only;
- identify product-quality gaps;
- run a baseline PPTX smoke using existing code;
- keep RF2.2 scope narrow and evidence-driven.

## Sources inspected by RF2.1

The RF2.1 checker inspects the repository itself, including:

- `backend/app/services/slides_service/outline.py`;
- `backend/app/services/slides_service/service.py`;
- `backend/app/services/slides_service/entrypoint.py`;
- `backend/app/services/slides_service/generator.py`;
- `backend/app/services/slides_service/plan_snapshot.py`;
- `backend/app/services/slides_service/revision.py`;
- `backend/app/api/routes/presentations.py`;
- `backend/app/services/presentation_catalog_service.py`;
- `frontend/src/lib/api/presentations.ts`;
- `frontend/src/components/presentations/slides-plan-editor-panel.tsx`;
- `frontend/tests/e2e/slides-plan-editor-smoke.spec.ts`;
- `backend/tests/services/test_slides_service.py`.

## Baseline runtime that is currently present

RF2.1 classifies these capabilities as `baseline_runtime_ready` when the checker and smoke pass:

1. `SlidesService.generate_deck` can build a deterministic plan from source text.
2. `generate_pptx_from_plan` can produce an OpenXML PPTX byte payload.
3. The generated payload starts as a ZIP/PPTX payload and contains core OpenXML presentation parts.
4. Local deterministic slide image generation exists through `DeterministicPatternImageProvider`.
5. Generated slide media can be registered when the service receives session/task context and a registry.
6. Local template registry exposes multiple local templates.
7. Presentation catalog API routes exist for listing presentations, versions, current plan, version plan, and plan diff.
8. Frontend plan editor and E2E smoke surface exist.

This is useful, but it is still a baseline deterministic runtime, not Kimi-grade deck generation.

## Partial runtime baseline

RF2.1 classifies these as partial runtime:

1. Presentation and version catalog metadata exists, but RF2 still needs a product-grade generate-from-approved-plan path.
2. Plan snapshot retrieval and diff routes exist, but RF2 still needs tighter runtime wiring for plan approval and retry lifecycle.
3. Existing services can generate PPTX from source text or a plan, but RF2 still needs an explicit approved-plan generation API/runtime path.
4. Template selection exists, but RF2 still needs adaptive/template metadata hardening in generated artifacts.
5. Artifact history exists in the broader project, but generated slides still need a strong source-to-artifact provenance path.

## Product-quality gaps

RF2.1 explicitly records these gaps:

1. No evidence yet of Kimi-like planning quality.
2. No operator-approved plan generation endpoint is proven.
3. No full plan approval to artifact registration lifecycle is proven.
4. No downloadable provenance manifest is emitted for generated decks.
5. No persistent slides task event stream is proven.
6. No visual QA runtime is implemented.
7. No proof that layouts handle rich real-world decks beyond deterministic smoke examples.
8. No LLM-backed local GigaChat plan generation path is proven in RF2.1.
9. No end-to-end Kimi-level product loop is proven across source intake, planning, editing, rendering, provenance, QA, retry, and operator gates.

## Contract-only or not-yet-runtime RF2 work

RF2.1 keeps these as future runtime work:

1. Actual source-to-artifact provenance manifest as a generated/downloadable artifact.
2. Full task event stream persistence for slides generation lifecycle.
3. Saved-plan retry runtime path from operator instruction.
4. Visual QA execution runtime.
5. Browser evidence runtime.
6. LLM-dependent approved plan generation path with local GigaChat integration.

## Baseline smoke

The checker runs an in-process smoke using existing slides service code:

```bash
python3 scripts/kw_slides_runtime_inventory_check.py \
  --repo-root . \
  --require-ready \
  --json
```

The smoke validates:

- no network required;
- no dependency or runtime changes;
- `SlidesService.generate_deck` returns a PPTX-like byte payload;
- the payload starts with `PK`;
- core OpenXML files exist;
- slide XML count matches the service result;
- the generated deck has at least one media asset;
- source grounding metadata is present;
- Kimi-grade support remains explicitly false.

## RF2.2 handoff

After RF2.1 acceptance, the recommended next step is:

RF2.2 — Minimal deterministic PPTX generation from approved plan.

RF2.2 should use RF2.1 evidence to stay narrow:

- use existing generator/service instead of rewriting renderer;
- add only the minimal runtime/API/persistence surface needed for approved-plan generation;
- preserve artifact registration, plan snapshots, and safe metadata requirements;
- do not introduce internet dependency or cloud LLM dependency;
- do not overclaim Kimi-level output until real product-quality gates exist;
- do not run `npm audit fix --force`.

## Acceptance

RF2.1 is accepted when:

- this inventory document exists;
- `kw_slides_runtime_inventory_check.py --require-ready` passes;
- baseline PPTX smoke passes;
- RF2.1 smoke tests pass;
- selected existing slides service smoke test still passes;
- S3-S7 slides contract checks still pass;
- RF2.0 checkpoint check still passes;
- production readiness includes RF2.1;
- full post-RF2.1 runner passes;
- Docker runtime smoke with `--skip-build` passes;
- remote `7_Runtime_Foundation` matches the local RF2.1 verdict commit;
- working tree is clean after cleanup.
