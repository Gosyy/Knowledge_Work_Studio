# Slides Kimi-level product gap audit

## Purpose

This document records the accepted product-quality audit for the KW Studio Slides pillar after KR-6D. It is intentionally not a history log. It defines the gap between the current KW Studio Slides implementation and the target professional presentation level inspired by Kimi Slides.

The target is not to copy Kimi internals. Public Kimi Slides documentation describes product capabilities, not internal architecture. KW Studio must build an offline/intranet implementation that reaches comparable professional outcomes under stricter constraints:

- no public internet in production/offline mode;
- no generated images;
- source-backed image reuse only;
- GigaChat is the only LLM runtime;
- local deterministic tools must be inspectable and validated;
- every claim, asset and chart must be traceable or explicitly marked as unsupported.

## Source references used for this audit

Primary public references:

- Kimi Slides product page: https://www.kimi.com/features/slides
- Kimi API chat/completions docs: https://platform.kimi.ai/docs/api/chat
- Kimi API JSON mode guide: https://platform.kimi.ai/docs/guide/use-json-mode-feature-of-kimi-api
- Kimi API official tools guide: https://platform.kimi.ai/docs/guide/use-official-tools
- PptxGenJS documentation: https://gitbrent.github.io/PptxGenJS/
- PptxGenJS charts documentation: https://gitbrent.github.io/PptxGenJS/docs/api-charts/
- React Flow documentation: https://reactflow.dev/
- Slidev documentation: https://sli.dev/guide/
- Slidev exporting documentation: https://sli.dev/guide/exporting
- PPTAgent repository: https://github.com/icip-cas/PPTAgent
- PresentAgent-2 repository: https://github.com/AIGeeksGroup/PresentAgent-2
- PptxGenJS repository: https://github.com/gitbrent/PptxGenJS
- React Flow / xyflow repository: https://github.com/xyflow/xyflow
- Slidev repository: https://github.com/slidevjs/slidev
- AIFixed reference project archive supplied by the operator: `AIFixed-main.zip`

Use these references as product and engineering inputs, not as permission to copy code blindly. Any code imported from external projects must pass license review, architecture review, dependency review and offline-runtime review first.

## Kimi Slides capability model inferred from public documentation

Kimi Slides publicly describes the following capabilities:

1. Text to slides: user describes an idea or pastes content; Kimi turns it into a clear structured outline and a professional deck with designer-grade formatting.
2. Documents to slides: PDF, Word, Excel and Markdown can be parsed into structured slides while preserving key details and embedded images.
3. Templates to branded slides: uploaded PowerPoint templates are understood through slide master, fonts and grid system.
4. Images to slides: photos, screenshots and design references can be turned into editable slides by recreating layout, structure and visual style.
5. Research-backed content: Kimi gathers information, structures it, and adds on-slide citations.
6. Designer-grade layouts: polished decks with balanced spacing and modern aesthetics.
7. Native diagrams and charts: complex diagrams and charts are rendered as native editable components rather than static images.
8. Editable export: text, images, shapes, charts and diagrams are editable; export options include PowerPoint, Google Slides and PNG.
9. Scenario packs: pitch decks, strategy, work reports, marketing/sales, education/training, academic/research with frameworks such as TAM/SAM/SOM, SWOT, strategic roadmaps, Gantt charts, KPI bars, funnels, trend lines, mind maps, formulas, scatter plots and distribution curves.

KW Studio must treat these as target product capabilities, not as claims that the current project already satisfies them.

## Current KW Studio Slides state

KR-6D is an important infrastructure milestone. It established that real GigaChat planning can return a validated schema and avoid deterministic fallback in `public_internet_test` mode.

Current strengths:

- source-mode routing exists;
- GigaChat public test mode exists;
- `slides_plan.v1` typed validation and repair retry exist;
- public text leakage checks exist for known placeholders;
- render/visual QA bundle and project runners exist;
- task/session/artifact pipeline exists;
- downloaded PPTX artifacts are produced and smoke-tested.

Current product-quality limits:

- the LLM contract is still mostly `title + bullets`, not a professional deck architecture;
- slide types are largely positional, not content-driven;
- fake charts are derived from bullet text length rather than real data;
- deterministic pattern images are synthetic decorative artifacts, not source-backed media;
- no professional visual planner exists;
- no data-backed chart extraction/binding exists;
- no source image relevance selection exists;
- no template/master analysis exists;
- no native editable chart/table/diagram renderer path exists at Kimi level;
- no dedicated presentation editor UI exists that is decoupled from backend by a stable API contract;
- QA proves technical renderability, not professional content/design/coherence.

## Module-level gap matrix

### SlidesService routing

Current role: route prompt-only presentation requests to the KR-6D user prompt planner and other source-aware flows to legacy planners.

Gap: routing is contract-aware, but it does not route into a full professional presentation pipeline with evidence retrieval, visual planning, asset selection, render strategy and editor lifecycle.

Required direction: keep source-mode contracts, but route professional Slides work into a PresentationIR pipeline.

### User prompt planning

Current role: `slides_plan.v1`, strict JSON validation, repair retry, metadata.

Gap: schema validates existence and basic quality of titles/bullets; it does not encode objective, audience, scenario, slide role, takeaway, evidence, content blocks, data needs, image needs, chart policies, layout intent or professional quality requirements.

Required direction: evolve into `presentation_ir.v1` and later `presentation_ir.v2`.

### Outline and structured blocks

Current role: typed blocks exist for bullet, comparison, timeline, table, chart and metrics.

Gap: comparison splits bullet lists; timeline maps bullets to phases; chart/metric values can be derived from text length; this is not a professional semantic visual system.

Required direction: introduce a Visual Grammar Library with explicit business frameworks, validators and source/data binding.

### Image pipeline

Current role: deterministic local pattern image generation for offline tests.

Gap: synthetic hash-pattern images look like arbitrary lines and undermine professional quality. The project must not generate images.

Required direction: remove deterministic generated images from professional path; use only source-backed images extracted from uploaded files or templates.

### Generator and layout

Current role: manual OOXML generation with static layouts and a small template registry.

Gap: renderer is useful for MVP validation but not enough for native editable charts, advanced tables, branded masters, 16:9 professional composition, or rich editor compatibility.

Required direction: add a renderer worker around PptxGenJS or equivalent, keep manual OOXML only as legacy/low-level fallback.

### Source grounding

Current role: honest text/outline grounding and citations when source refs exist.

Gap: no full document-to-slides pipeline: no robust image/table/chart extraction and selection, no evidence coverage scoring, no visual reuse policy.

Required direction: build offline source ingestion and evidence retrieval before claiming document-to-slides quality.

### UI

Current role: current KW Studio UI is a workspace shell, not a professional presentation studio.

Gap: Kimi-like editing requires slide thumbnails, canvas, block inspector, asset tray, citations panel, quality warnings, plan review and export management.

Required direction: build an independent API-first Presentation Studio frontend. AIFixed can be used as an editor donor only after audit.

## Non-goals until explicitly accepted

Do not claim:

- Kimi-level Slides quality;
- complete offline parity with Kimi;
- research-backed content without source evidence;
- generated image capability;
- full PowerPoint template understanding;
- full Excel/chart understanding;
- native editable chart/diagram coverage unless renderer and QA prove it;
- public GigaChat test evidence as offline/intranet proof.

## Immediate consequence

KR-6D must be described as: validated and repairable GigaChat slide planning infrastructure. It is not professional deck generation.
