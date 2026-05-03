# KW Studio RF Exit Criteria for K-Phase

## Status

RF_closure is accepted. K-phase may now start with K0 on branch `8_K_Phase`; K0 remains evaluation-only and does not claim Kimi-level support.

RF2.2a establishes RF exit criteria for entering K-phase.

This document is a planning/checkpoint guard. It does not change runtime behavior.

## Accepted default

The project must finish RF before entering K-phase product-power work.

RF is not expected to reach Kimi-level slides quality. RF is expected to create the stable offline runtime foundation that allows K-phase to work safely.

## Required RF closure

K-phase may start only after these conditions are true.

### RF1 — Offline/operator foundation

RF1 must remain accepted:

- offline dependency inventory;
- offline bootstrap bundle strategy;
- manifest validation;
- bundle verification CLI;
- artifact presence checks;
- checksum integrity;
- inventory summaries;
- readiness report;
- operator command groups;
- controlled dependency/security assessment;
- no uncontrolled `npm audit fix --force`.

### RF2 — Slides runtime foundation

RF2 must close at least:

- RF2.0 slides runtime phase checkpoint;
- RF2.1 runtime capability inventory and baseline smoke;
- RF2.2 approved-plan deterministic PPTX runtime;
- RF2.3 plan snapshot persistence and task event stream runtime wiring;
- RF2.4 saved-plan retry runtime path;
- RF2.5 adaptive/template local render mode runtime hardening;
- RF2.6 provenance manifest emitted as downloadable artifact;
- RF2.7 slides generation lifecycle UX polish;
- RF2 closure checkpoint.

### RF3 — Real document ingestion foundation

RF3 must close:

- real DOCX text extraction;
- real PDF text extraction;
- honest scanned/image-only PDF failure modes;
- source metadata for extracted content;
- artifact/provenance hooks;
- no fake OCR claims;
- no cloud OCR dependency.

### RF4 — Local GigaChat integration hardening

RF4 must close:

- direct local GigaChat configuration validation;
- endpoint diagnostics;
- timeouts;
- mocked success/failure tests;
- no silent fallback;
- no silent LiteLLM override;
- operator-readable failure states.

## Global acceptance gates

Before K-phase starts:

- production readiness gate passes;
- full KWS runner passes;
- Docker runtime smoke with `--skip-build` passes;
- branch `7_Runtime_Foundation` remote matches local verdict commit;
- working tree is clean after cleanup;
- generated env/proxy/log/cache artifacts are not committed.

## K-readiness matrix

| Area | RF exit target | K-phase target |
| --- | --- | --- |
| Slides planning | Structured/baseline runtime and local GigaChat-ready path | High-quality source-aware story planning |
| Rendering | Deterministic PPTX from approved plan | Layout engine, visual hierarchy, charts/tables, overflow prevention |
| UX | Plan approval, generation lifecycle, retry hooks | Kimi-like planning cockpit and review loop |
| Provenance | Downloadable source-to-artifact manifests | Slide-level source traceability |
| Visual QA | Runtime hooks and planning | Preview/rendered-slide QA loop |
| Documents | Real DOCX/PDF extraction foundation | Source-aware deck generation from real files |
| LLM | Direct local GigaChat hardened | Strong planner and prompt orchestration |
| Offline deployment | Reproducible operator bootstrap | Product-power features without internet dependency |

## RF must not absorb K-phase

RF must not become open-ended product-power work.

If a task is about story quality, layout quality, visual intelligence, rich planning, or Kimi-like UX, it belongs in K-phase unless it is required to finish RF wiring.

## Next default sequence

From RF2.2 accepted, default sequence is:

1. RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap;
2. RF2.3 — Plan snapshot persistence and task event stream runtime wiring;
3. RF2.4 — Saved-plan retry runtime path;
4. RF2.5 — Adaptive/template local render mode runtime hardening;
5. RF2.6 — Slides provenance manifest emitted as downloadable artifact;
6. RF2.7 — Product UX polish for slides generation lifecycle;
7. RF2 closure;
8. RF3;
9. RF4;
10. RF closure;
11. K0.
