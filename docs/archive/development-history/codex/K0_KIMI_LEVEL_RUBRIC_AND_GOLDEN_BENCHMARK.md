# K0 — Kimi-level Rubric and Golden Deck Benchmark

## Status

K0 starts K-phase on branch `8_K_Phase` after accepted `RF_closure` at `a52f038b0fb651e3b33c33f999ca9ba0d615bff9`.

K0 does not claim that KW Studio already reaches Kimi-level. K0 defines the measurable rubric, golden benchmark cases, scoring thresholds, and no-overclaim gates that later K-phase work must pass.

## Purpose

K0 turns the Kimi-level target into an explicit benchmark contract.

Kimi-level means the whole slides product loop:

source intake -> source understanding -> local/offline GigaChat planning -> outline-first UX -> editable plan -> approved-plan generation -> adaptive/template rendering -> visual hierarchy -> artifact history -> source-to-artifact provenance -> visual QA -> retry lifecycle -> operator-visible task events -> reproducible offline deployment.

## Rubric dimensions

The K0 rubric contains exactly ten weighted dimensions whose weights sum to 100:

1. Storyline quality — 12
2. Slide hierarchy — 10
3. Layout consistency — 10
4. Visual density control — 8
5. Source faithfulness — 12
6. Editability — 8
7. Retry quality — 8
8. Visual QA result — 8
9. Provenance quality — 12
10. Offline reproducibility — 12

A future Kimi-level candidate must reach an overall weighted score of at least 85.

## Golden benchmark cases

K0 defines five local benchmark cases:

- source memo to executive deck;
- technical document to architecture deck;
- project log to status deck;
- comparison table to decision deck;
- long DOCX/PDF to structured presentation.

The benchmark cases are evaluation contracts. K0 does not yet implement the full Kimi-like workflow and does not assert that generated decks pass these cases.

## Non-goals

K0 does not:

- improve the renderer;
- add visual QA runtime;
- add a new public API endpoint;
- add DB schema migrations;
- change Dockerfiles;
- change dependency versions;
- switch away from direct local GigaChat-first production topology;
- make LiteLLM mandatory;
- run `npm audit fix` or `npm audit fix --force`;
- claim Kimi-level support.

## Acceptance

K0 is accepted when:

- branch `8_K_Phase` starts from accepted `RF_closure`;
- K0 rubric dimensions and benchmark cases are present;
- checker reports `kimi_level_claimed_by_k0: false`;
- checker reports `whole_project_kimi_level_supported: false`;
- K0 smoke tests pass;
- production readiness includes K0;
- full runner and Docker runtime smoke pass after commit/push.

## Next step

After K0 acceptance, the default next step is K1 — Local GigaChat planning engine.
