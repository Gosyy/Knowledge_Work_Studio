# KR-7 Kimi-level Slides roadmap for KW Studio

## Mission

Build a professional offline/intranet Slides workflow approaching the product outcomes publicly claimed by Kimi Slides, while respecting KW Studio constraints:

- production/offline mode has no public internet;
- GigaChat is the only LLM runtime;
- no generated images;
- images can only be selected from uploaded documents, templates or user-provided assets;
- charts must be backed by real extracted or user-provided numeric data;
- diagrams must be native/editable shapes, not decorative screenshots;
- all artifacts must be provenance-first and quality-gated;
- UI must be independent from backend and consume backend only through a stable API contract.

## Target architecture

```text
Presentation Studio UI
  -> OpenAPI client
  -> KW Studio Presentation API
  -> source ingestion / asset registry / evidence index
  -> GigaChat planning adapter
  -> PresentationIR planner
  -> visual grammar planner
  -> render worker
  -> render/visual/content QA
  -> artifacts, versions, provenance
```

## Canonical future contract: PresentationIR

The next major Slides contract must not be a flat list of titles and bullets. It must represent a professional deck.

Sketch:

```json
{
  "schema_version": "presentation_ir.v1",
  "deck": {
    "title": "string",
    "objective": "string",
    "audience": "executive|technical|sales|education|research|general",
    "tone": "string",
    "scenario": "strategy|pitch|report|training|research|sales|custom",
    "language": "ru",
    "slide_count": 6
  },
  "theme": {
    "template_id": "business_clean",
    "brand_source": "uploaded_template|system_template|none",
    "font_family": "Aptos",
    "color_tokens": {}
  },
  "sources": [],
  "assets": [],
  "slides": [
    {
      "slide_id": "s001",
      "slide_number": 1,
      "role": "cover|executive_summary|problem|insight|solution|roadmap|data|decision|closing",
      "title": "string",
      "takeaway": "one sentence",
      "evidence": [],
      "blocks": [
        {
          "block_id": "b001",
          "type": "text|bullets|kpi_cards|timeline|roadmap|comparison|matrix|swot|chart|table|diagram|image",
          "semantic_role": "main_claim|supporting_evidence|visual_explanation",
          "content": {},
          "data_binding": null,
          "source_refs": []
        }
      ],
      "visual_plan": {
        "layout_family": "cover|split|dashboard|matrix|timeline|roadmap|editorial|minimal",
        "density": "low|medium|high",
        "requires_image": false,
        "requires_chart": false,
        "requires_diagram": false,
        "allowed_without_data": true
      },
      "speaker_notes": "string"
    }
  ],
  "quality_contract": {
    "no_fake_charts": true,
    "no_generated_images": true,
    "source_images_only": true,
    "native_editable_components": true
  }
}
```

## Phase KR-7A — document product gap and roadmap

Goal: lock the audit and roadmap before new code.

Steps:

1. Add this roadmap.
2. Add the Kimi-level gap audit.
3. Update `PROJECT_MIGRATION_HANDOFF.md`.
4. Update `README.md` and `AGENTS.md` with links.
5. Add assistant engineering guidance for external code/repo use.
6. Add a test portfolio rationalization plan.

Acceptance:

- docs exist and are internally linked;
- unsupported claims are avoided;
- handoff checker passes;
- `git diff --check` passes;
- full runner and Docker smoke must pass before remote acceptance.

## Phase KR-7B — GigaChat-only LLM cleanup

Goal: remove local small LLM as a runtime/product concept.

Steps:

1. Audit every `ollama`, local model, fake provider and noop provider reference.
2. Remove production/deploy config for local LLMs.
3. Keep fake/test providers only as explicit test doubles.
4. Update readiness and topology checkers.
5. Remove UI model selector options that imply arbitrary local LLMs.
6. Update docs and tests.

Acceptance:

- production/readiness fails closed if LLM provider is not GigaChat;
- tests use dependency overrides, not production settings;
- no `.env.deploy.example` production local LLM route remains;
- public GigaChat test mode remains explicit and warning-bearing.

## Phase KR-7C — API-first Presentation contract

Goal: backend becomes usable by any interface through a stable API.

Endpoints to design:

```text
POST   /api/v1/presentations
POST   /api/v1/presentations/{id}/sources
POST   /api/v1/presentations/{id}/plan
GET    /api/v1/presentations/{id}
GET    /api/v1/presentations/{id}/slides
PATCH  /api/v1/presentations/{id}/slides/{slide_id}
POST   /api/v1/presentations/{id}/render
POST   /api/v1/presentations/{id}/export
GET    /api/v1/presentations/{id}/quality
GET    /api/v1/artifacts/{artifact_id}/download
```

Acceptance:

- OpenAPI schema generated;
- typed frontend client can be generated;
- old `/tasks` slides path remains as compatibility adapter;
- PresentationIR versioning exists;
- UI can be replaced without backend changes.

## Phase KR-7D — offline source ingestion engine

Goal: build document understanding without internet.

Required extractors:

- DOCX: headings, paragraphs, tables, inline images, captions, styles;
- PDF: pages, text blocks, tables, embedded images, coordinates, page thumbnails when needed;
- XLSX/CSV: sheets, tables, formulas, chart data candidates, images/drawings;
- PPTX: slides, text boxes, shapes, groups, tables, images, charts, themes, masters, layouts;
- Markdown: headings, tables, code blocks, image refs.

Candidate tools:

- `python-docx`;
- `python-pptx`;
- `PyMuPDF` / `pymupdf`;
- `pdfplumber`;
- `openpyxl`;
- `Pillow`;
- `lxml`;
- LibreOffice headless;
- poppler utilities.

Acceptance:

- source assets are extracted with provenance;
- images are stored in `SourceAssetRegistry`;
- tables become structured candidates;
- unsupported extraction is reported honestly.

Implementation note after KR-7D.1:

```text
KR-7D.1 introduces a deterministic offline source ingestion engine foundation.
It extracts Markdown/text fragments, Markdown/CSV/XLSX table previews, DOCX paragraphs/tables/media assets, PPTX slide text/media assets, and XLSX formulas/table candidates with provenance references.
It emits source_ingestion_provenance.v1 and source_asset_registry.v1 reports.
PDF extraction is dependency-gated through PyMuPDF/fitz when available and returns unsupported instead of fake OCR/text when unavailable.
It does not implement evidence retrieval, embeddings, OCR, source-to-slide planning, render, export, or quality scoring.
```

Implementation note after KR-7D.2:

```text
KR-7D.2 adds SourceAssetRegistry persistence and extracted asset storage.
It stores extracted asset bytes under a caller-provided storage root, writes source_asset_storage.v1 manifests, verifies checksums, exposes source-asset:// URIs and relative paths only, and keeps ingestion report JSON free of raw content bytes.
It does not implement evidence retrieval, embeddings, OCR, source-to-slide planning, render, export, quality scoring, or UI source management.
```

Implementation note after KR-7D.3:

```text
KR-7D.3 enriches offline document structure extraction inside the ingestion engine.
It emits source_structure.v1 elements for Markdown headings/code/image refs, DOCX styles/captions/tables/images, PPTX slides/text boxes/tables/charts, XLSX worksheets/formulas/chart data candidates, and PDF page/text block coordinates when PyMuPDF/fitz is available.
It does not implement KR-7E evidence retrieval, embeddings, OCR, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management.
```

Implementation note after KR-7D.4:

```text
KR-7D.4 hardens real package extraction fidelity and dependency-backed extractors.
It adds source_extraction_fidelity.v1 metadata, records optional dependency availability, resolves OOXML package relationships for DOCX/PPTX media, preserves relationship-aware source asset metadata, and reports image dimensions when Pillow can read the embedded bytes.
It does not implement KR-7E evidence retrieval, embeddings, OCR, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management.
```

## Phase KR-7E — offline evidence retrieval

Goal: replace web research with local source-backed evidence.

Methods:

- PostgreSQL full-text search;
- BM25 / `rank_bm25`;
- lexical entity/keyword extraction;
- source section scoring;
- no hidden local embedding LLM dependency.

Acceptance:

- every source-backed slide can list evidence fragments;
- unsupported claims are flagged;
- no research-backed claim is made for prompt-only decks without sources.

Implementation note after KR-7E.1:

```text
KR-7E.1 introduces an offline evidence index foundation.
It builds offline_evidence_index.v1 from KR-7D ingestion reports using lexical_token_index, BM25-like IDF scoring, and source section scoring over local fragments, tables, structures, and chart candidates.
It flags unsupported claims, preserves provenance refs, and ensures prompt-only decks must not be treated as research-backed.
It does not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management.
```

Implementation note after KR-7E.2:

```text
KR-7E.2 hardens evidence-to-source-section scoring and unsupported-claim reporting.
It adds source section scores, claim-term coverage ratios, missing-term detection, and offline_unsupported_claim_report.v1 payloads with candidate sections and required operator action.
It does not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management.
```

Implementation note after KR-7E.3:

```text
KR-7E.3 adds evidence index persistence and retrieval API read contract.
It persists offline_evidence_index.v1 to offline_evidence_index_storage.v1 manifests, verifies checksums, exposes safe read-only /api/v1/presentations/{id}/evidence endpoints, and keeps evidence search/claim assessment backed by persisted local source evidence.
It does not implement PostgreSQL FTS runtime, embeddings, web research, source-to-slide planning, PresentationIR planning, render/export, quality scoring, or UI source management.
```

## Phase KR-7F — PresentationIR planner

Goal: use GigaChat to produce professional deck architecture.

Planner layers:

1. deck strategy planner;
2. slide role planner;
3. block planner;
4. visual planner;
5. evidence binder;
6. QA expectation builder.

Acceptance:

- every slide has role, takeaway, blocks and visual plan;
- charts require real numeric data;
- images require source assets;
- fallback is degraded and explicit;
- no invented evidence.

Implementation note after KR-7F.1:

```text
KR-7F.1 introduces a deterministic PresentationIR planner foundation through presentation_ir_planner.v1.
It consumes KR-7E offline evidence, emits validated presentation_ir.v1 drafts with slide roles, takeaways, blocks, visual plans, evidence bindings, and explicit ready/degraded/blocked status.
It does not implement final GigaChat planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime.
```

## Phase KR-7G — visual grammar library

Goal: first professional editable blocks.

Blocks:

- executive summary cards;
- KPI cards;
- process flow;
- roadmap;
- timeline;
- 2x2 matrix;
- SWOT;
- comparison table;
- decision matrix;
- risk matrix;
- architecture diagram;
- funnel;
- data table;
- native chart from real data.

Acceptance:

- every block has semantic purpose and validator;
- chart has data source ref;
- diagram has nodes/edges/items;
- fake chart values are forbidden.

Implementation note after KR-7G.1:

```text
KR-7G.1 introduces presentation_visual_grammar.v1 as the first visual grammar library foundation.
It defines professional editable block specs and validators for executive summary cards, KPI cards, process flow, roadmap, timeline, 2x2 matrix, SWOT, comparison table, decision matrix, risk matrix, architecture diagram, funnel, data table, and native chart from real data.
It enforces semantic purpose, source refs, diagram nodes/items, and native_chart real numeric source data refs; fake chart values are forbidden.
It does not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, or UI runtime.
```

## Phase KR-7H — native PPTX renderer worker

Goal: move professional render path to a renderer capable of native components.

Candidate: PptxGenJS worker.

Architecture:

```text
Python backend builds PresentationIR
-> Node renderer worker receives JSON
-> PptxGenJS creates native PPTX
-> LibreOffice renders PDF/PNG proof
-> backend stores artifact bundle
```

Acceptance:

- 16:9 default;
- native charts/tables/shapes;
- source images only;
- PPTX editable in PowerPoint/LibreOffice;
- render and quality reports pass.

## Phase KR-7I — template and brand understanding

Goal: use uploaded PPTX templates as brand/layout sources.

Steps:

- parse slide size;
- parse theme colors;
- parse fonts;
- parse masters/layouts/placeholders;
- extract logos/backgrounds;
- build `TemplateProfile`;
- map PresentationIR slide roles to template layout families.

Acceptance:

- template style is used without blindly copying old content;
- unsupported template features are warned;
- generated deck stays within template grid/style constraints.

## Phase KR-7J — source image selection

Goal: reuse images from uploaded docs/templates only.

Image features:

- dimensions;
- aspect ratio;
- source page/slide/sheet;
- nearby text;
- caption;
- checksum/phash;
- quality score.

Acceptance:

- every image has source citation;
- no random image;
- no generated image;
- if no relevant image exists, the slide remains typographic or diagrammatic.

## Phase KR-7K — data-backed charts

Goal: charts only from real data.

Steps:

- extract data candidates from XLSX/CSV/PDF/DOCX/PPTX;
- classify chart intent;
- validate numeric series;
- bind chart to data source ref;
- render native chart.

Acceptance:

- chart without data source is rejected;
- labels and values are traceable;
- units are captured or marked unknown;
- no bullet-length charts.

## Phase KR-7L — professional layout engine

Goal: replace fixed-box MVP layouts with a layout solver.

Features:

- 16:9 default;
- design tokens;
- typographic scale;
- grid, margins, gutters;
- layout families;
- text fitting;
- overlap detection;
- contrast and density checks.

Acceptance:

- no clipped titles;
- no overlapping shapes;
- readability/contrast/density score exists;
- rendered PNG QA passes.

## Phase KR-7M — Presentation Studio UI

Goal: independent frontend connected only by API.

Use AIFixed as a UI donor for:

- slide editor shell;
- thumbnails;
- DnD blocks;
- theme selector;
- undo/redo;
- chart/table editors;
- block inspector concepts;
- PptxGenJS mapping ideas.

Do not reuse from AIFixed:

- backend runtime;
- local model layer;
- Qdrant/embedding layer;
- arbitrary model selector;
- frontend-side generation as source of truth;
- hardcoded local/default models.

Acceptance:

- UI can run separately;
- backend URL configurable;
- OpenAPI client used;
- edits persist through backend API;
- export is backend-side.

## Phase KR-7N — professional quality evaluator

Goal: evaluate content, design and coherence.

Quality axes:

- content: objective, takeaway, evidence, no filler;
- design: alignment, density, contrast, hierarchy, clipping;
- coherence: story arc, repetition, order, role consistency;
- data: chart source, labels, units, no invented numbers;
- assets: source-backed relevance, no decorative garbage;
- export: PPTX opens, PDF/PNG render proof.

Acceptance:

- `quality_report.json` has scores and blockers;
- Kimi-level/professional status requires quality pass;
- degraded decks are marked degraded.

## Phase KR-7O — scenario packs

Goal: offline professional scenario-specific decks.

Packs:

- strategy;
- pitch;
- report;
- sales/marketing;
- education;
- research.

Acceptance:

- scenario is detected or selected;
- proper visual grammar is used;
- missing data blocks invalid charts;
- no invented TAM/SAM/SOM, financials or KPI values.

## Phase KR-7P — template clone/rewrite mode

Goal: rewrite all text blocks in uploaded PPTX while preserving design.

Steps:

- parse every text shape/table cell/group;
- classify shape role;
- rewrite all text blocks with length constraints;
- preserve style and geometry;
- reuse source images/layouts;
- render QA.

Acceptance:

- all text blocks rewritten unless explicitly locked;
- source text does not leak;
- geometry preserved;
- no overlaps/clipping;
- PPTX render passes.

## Phase KR-7Q — offline Kimi-like source-backed generation

Goal: generate decks from uploaded materials with evidence, assets and data.

Pipeline:

```text
upload sources
-> extract text/tables/images
-> build evidence pack
-> PresentationIR planning
-> visual planning
-> source image/data binding
-> native renderer
-> quality gates
-> editor preview/export
```

Acceptance:

- high evidence coverage;
- source images only;
- data-backed charts only;
- quality pass before professional claim.

## Phase KR-7R — public GigaChat quality harness

Goal: use public GigaChat test mode to validate planning quality without treating it as offline proof.

Acceptance:

- secret-safe logs;
- `public_internet_test` warning preserved;
- fixed benchmark decks generated;
- PresentationIR validation passes;
- quality metrics recorded.

## Phase KR-7S — legacy cleanup

Goal: remove or quarantine MVP surfaces that block professional quality.

Targets:

- deterministic pattern image provider from professional path;
- fake chart weights;
- old local LLM provider runtime configs;
- markdown-only slide generation assumptions;
- manual OOXML renderer as default professional path.

Acceptance:

- backward compatibility tests retained where needed;
- cleanup is controlled and documented;
- full runner and Docker smoke pass.

## Phase KR-7T — final Kimi-level acceptance definition

A deck can be called Kimi-level only after:

- text-to-slides produces professional executive deck;
- document-to-slides is source-backed;
- template-to-branded-slides uses real template profile;
- charts/tables/diagrams are native and editable;
- images are source-backed;
- UI supports plan review and slide editing;
- quality evaluator passes content/design/coherence/data/assets/export gates;
- public GigaChat evidence exists;
- full runner and Docker smoke pass;
- unsupported claims are absent.

## Recommended implementation order

```text
KR-7A docs and test audit
KR-7B GigaChat-only cleanup
KR-7C API-first PresentationIR
KR-7D/E source ingestion and evidence retrieval
KR-7F/G planner and visual grammar
KR-7H renderer worker
KR-7J/K/L images, charts, layout
KR-7M UI
KR-7N/R quality evaluator and public test harness
KR-7P/Q/T clone/rewrite, source-backed generation, final acceptance
```
## KR-7F.2 evidence-aware slide outline planning hardening

KR-7F.2 hardens evidence-aware slide outline planning on top of the deterministic KR-7F.1 PresentationIR planner foundation. It adds `presentation_ir_outline.v1` slide outlines, role-specific evidence queries, per-slide support status, coverage ratios, missing terms, and explicit unsupported/weak slide outline warnings.

Validation surface:

```text
backend/app/services/slides_service/presentation_ir_planner.py defines PRESENTATION_IR_OUTLINE_SCHEMA_VERSION and PresentationIRSlideOutline;
PresentationIRPlannerResult exposes slide_outlines and coverage_summary;
PresentationIR slides include outline metadata and quality_contract records evidence_aware_outline_planning and outline coverage counts;
backend/tests/services/test_kr7f_presentation_ir_planner.py covers evidence-aware outlines, degraded low-coverage outlines, and prompt-only unsupported outlines;
scripts/kw_presentation_ir_planner_check.py verifies the KR-7F.2 surface.
```

Important limitation:

```text
KR-7F.2 is planner hardening only. It does not implement final GigaChat PresentationIR planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime. Unsupported slide outlines must remain explicit and must not be treated as source-backed.
```

Implementation note after KR-7F.3:

```text
KR-7F.3 hardens planner persistence and PresentationIR snapshot API contract.
It adds presentation_ir_planner_snapshot.v1 metadata, persistable planner result validation, blocked-result fail-closed persistence, and read-side planner snapshot metadata in PresentationIR API responses and version summaries.
It does not implement final GigaChat planning runtime, embeddings, web research, PostgreSQL FTS runtime, render/export, visual QA, quality scoring, or UI runtime.
```

Implementation note after KR-7G.2:

```text
KR-7G.2 binds visual grammar blocks into PresentationIR planner output. KR-7G.2 binds presentation_visual_grammar.v1 blocks into PresentationIR planner output through presentation_ir_visual_grammar_binding.v1.
It uses source-backed visual grammar blocks only when slide outlines have evidence bindings, records visual grammar validation status in block metadata and quality_contract, and keeps prompt-only/unsupported outlines explicitly blocked instead of pretending visual blocks are source-backed.
It does not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, quality scoring, or UI runtime.
```
