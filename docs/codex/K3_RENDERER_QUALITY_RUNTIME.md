# K3 Renderer Quality Runtime

K3 adds a controlled renderer-quality runtime layer for KW Studio on branch `8_K_Phase` after accepted K2 HEAD `48f8579adc9be176ce60cc1fa39fe5ad0b19f3a4`.

K3 is a renderer quality upgrade, not a Kimi-level claim.

## What K3 adds

K3 introduces `backend/app/services/k_phase/renderer_quality.py` as a local deterministic runtime layer over an approved `PresentationPlan`.

The runtime provides:

- deterministic layout selection from existing slide types, visual intent, and structured blocks;
- content density control for titles, bullets, tables, charts, comparison blocks, timelines, and metric cards;
- visual hierarchy metadata for title/subtitle/body balance;
- local theme pack resolution through the bundled template registry;
- overflow risk assessment before and after the K3 pass;
- safe render-quality metadata for acceptance checks;
- render-ready output that can still use the existing approved-plan PPTX runtime.

## Scope boundaries

K3 intentionally does not add:

- public API endpoint;
- database schema migration;
- frontend runtime change;
- dependency version change;
- Dockerfile or base image change;
- cloud LLM or public internet dependency;
- visual QA runtime, which remains K4;
- full source-to-slide provenance, which remains K5;
- whole-product Kimi-level support claim.

## Local/offline behavior

The runtime resolves template IDs only through the bundled local template registry. External template URLs, filesystem paths, downloads, and public internet access are outside K3 scope.

The K3 safe metadata reports `network_required=false` and keeps raw source text, prompts, and sensitive values out of render-quality metadata.

## Acceptance checker

`scripts/kw_k3_renderer_quality_check.py` verifies that K3:

- reports renderer-quality runtime capability;
- selects deterministic layout hints;
- bounds dense bullets and titles;
- bounds table rows/columns and chart categories;
- produces a render-ready PPTX through the approved-plan runtime;
- preserves offline/intranet constraints;
- does not claim Kimi-level;
- does not cross into K4 visual QA or K5 provenance runtime.

## Next phase

After K3 is accepted and full runner plus Docker smoke pass, the next controlled phase is K4: Visual QA runtime.
