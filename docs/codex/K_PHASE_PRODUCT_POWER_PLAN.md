# KW Studio K-Phase Product Power Roadmap

## Status

K0 is the first controlled patch on branch `8_K_Phase` after accepted `RF_closure`. It defines the Kimi-level rubric and golden deck benchmark, but it does not claim KW Studio already reaches Kimi-level.

RF2.2a establishes the default RF-to-K roadmap and Kimi-level product-power target.

This document is the accepted planning guard for the next major product phase after RF0-RF4. It does not start K-phase and does not change runtime behavior.

## Default route

The default project route is now:

1. finish RF0-RF4;
2. run RF closure;
3. enter K-phase only after RF exit criteria are met;
4. use K-phase for power-building work that moves KW Studio toward Kimi-level slides quality.

RF must remain a foundation/runtime-hardening phase. K-phase is the product-power phase.

## Kimi-level target

Kimi-level does not mean a single stronger PPTX generator.

Kimi-level means the whole slides product loop is strong:

source intake -> document understanding -> local/offline GigaChat planning -> outline-first UX -> editable plan -> approved-plan generation -> adaptive/template rendering -> layout and visual quality -> charts/tables/media -> artifact history -> source-to-artifact provenance -> visual QA -> retry lifecycle -> operator-visible task event stream -> reproducible offline deployment.

## Product power areas

K-phase must improve these areas as first-class product work:

### K0 — Kimi-level rubric and golden deck benchmark

Create local benchmark cases and quality scoring:

- source memo to executive deck;
- technical document to architecture deck;
- project log to status deck;
- comparison table to decision deck;
- long DOCX/PDF to structured presentation.

Score:

- storyline quality;
- slide hierarchy;
- layout consistency;
- visual density;
- source faithfulness;
- editability;
- retry quality;
- visual QA result;
- provenance quality;
- offline reproducibility.

### K1 — Local GigaChat planning engine

K1 status: local GigaChat planning runtime is implemented as a controlled K-phase foundation path. It remains below Kimi-level until later K2-K6 workflow, renderer, QA, and provenance benchmark gates pass.

Add a stronger offline planning engine:

- source understanding;
- audience and intent;
- story arc;
- slide-by-slide plan;
- evidence links;
- visual suggestions;
- speaker-note hints;
- deterministic fallback when LLM is unavailable.

### K2 — Plan editor as product workflow

K2 status: plan editor product workflow runtime is implemented as an operator-gated editable plan session. It remains below Kimi-level until K3-K6 renderer, visual QA, provenance, and benchmark gates pass.

Turn the plan editor into a real planning cockpit:

- outline tree;
- slide goals;
- evidence/source links;
- visual intent;
- render mode controls;
- approval gate;
- diff/retry workflow;
- clear failure states.

### K3 — Renderer quality upgrade

K3 status: renderer quality runtime is implemented as a local deterministic quality pass over an approved `PresentationPlan`. It improves layout selection, density control, visual hierarchy metadata, table/chart bounds, local theme-pack resolution, and overflow prevention. It remains below Kimi-level until K4 visual QA, K5 provenance, and K6 end-to-end workflow gates pass.

Improve slide output quality:

- layout selection engine;
- content density control;
- visual hierarchy;
- table/chart rendering;
- title/subtitle/body balance;
- template packs;
- local theme system;
- overflow prevention.

### K4 — Visual QA runtime

K4 status: visual QA runtime is implemented as a local deterministic PPTX OOXML inspection layer over K3-bounded rendered artifacts. It adds safe slide previews, layout bounds checks, major-overlap checks, estimated overflow checks, bundled-theme contrast checks, reading-order checks, and explicit operator review metadata. It remains below Kimi-level until K5 provenance and K6 end-to-end workflow gates pass.

Move from visual QA planning to runtime checks:

- PPTX render preview from local OOXML;
- layout checks;
- overflow checks;
- contrast checks;
- reading-order checks;
- operator review workflow.

K4 intentionally does not add cloud vision, a public API endpoint, a DB schema migration, frontend runtime changes, dependency changes, Dockerfile changes, or source-to-slide provenance.

### K5 — Source-to-slide provenance

Make every slide traceable:

- source references;
- plan decision links;
- render attempt metadata;
- artifact version;
- evidence bundle links;
- safe redaction.

### K6 — End-to-end Kimi-like workflow

Deliver the full loop:

upload sources -> plan -> edit -> approve -> generate -> QA -> revise -> export -> provenance bundle.

## Non-negotiable constraints

K-phase must preserve KW Studio identity:

- offline/intranet first;
- artifact-first;
- provenance-first;
- operator-gated;
- direct local GigaChat-first for production LLM;
- LiteLLM optional only;
- no silent cloud fallback;
- no internet-dependent default runtime;
- no broad autonomous browser agent;
- no file-format zoo;
- no microservice rewrite.

## Dependency/security rule

Do not run `npm audit fix --force` as part of K-phase feature work.

Any dependency/security remediation must be a separate controlled patch with:

- diff scope;
- lockfile/package analysis;
- targeted tests;
- full runner;
- rollback notes.

## K-phase entry condition

K-phase starts only after RF closure accepts:

- RF2 slides runtime foundation;
- RF3 real DOCX/PDF ingestion foundation;
- RF4 local GigaChat integration hardening;
- production readiness gate;
- full runner;
- Docker runtime smoke;
- K-phase roadmap;
- Kimi-level rubric;
- transition prompt for a new chat if context limit is near.

## Handoff rule

When moving development to a new chat, the migration prompt must include this K-phase plan, RF exit criteria, three-server topology, direct local GigaChat default, optional LiteLLM gateway, and the rule that RF must finish before K-phase starts.
