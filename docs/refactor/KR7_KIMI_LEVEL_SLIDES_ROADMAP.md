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

Agreed KR-7H consolidation plan after KR-7H.8:

```text
KR-7H.9  — minimal PresentationIR mapping + single/multi-slide temporary PPTX smoke
KR-7H.10 — persistent PPTX artifact bundle + render report contract
KR-7H.11 — LibreOffice proof bundle smoke
KR-7H.12 — renderer hardening: source-image-only, fail-closed, no fake artifacts
KR-7H.13 — KR-7H closure gate
```

Rationale:

- KR-7H.1 through KR-7H.8 intentionally de-risked the renderer boundary, worker package, PptxGenJS dependency, in-memory construction, temporary file output, and static-slide output in small steps;
- after KR-7H.8 the remaining KR-7H work should use larger patches when the scope stays inside one architectural layer and one validation contour;
- larger KR-7H patches are allowed only when the patch has clear non-goals, fail-closed behavior, exact local patch/package testing, targeted validation, full runner, Docker smoke, and reviewed logs;
- do not merge PresentationIR mapping, persistent artifact storage, LibreOffice proof generation, visual QA, UI changes, or GigaChat runtime changes into one patch unless the phase plan is explicitly revised again.

The post-KR-7H.8 plan above replaces the earlier open-ended micro-step continuation for remaining KR-7H work. Future KR-7H.* patches must follow this consolidation unless a later documented decision updates the plan.

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

Implementation note after KR-7I:

KR-7I adds `presentation_template_brand_profile.v1` as the first uploaded-PPTX template and brand understanding contract after the KR-7H renderer-worker foundation closure. The profile inspects PPTX OOXML/ZIP parts for slide size, theme colors, fonts, masters/layouts/placeholders, source media assets, role-to-layout-family hints, and unsupported-feature warnings. It explicitly keeps `no_template_clone_rewrite_mode`, old-template-content copying, no_production_layout_engine, renderer runtime changes, visual QA/scoring, source image selection runtime, image/chart/table mapping, UI changes, GigaChat/runtime changes, Docker/deploy/Postgres changes, and Kimi-level claims out of scope.

KR-7I validation includes `kw_template_brand_profile_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. The next phase remains KR-7J source image selection.

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

Implementation note after KR-7J:

KR-7J adds `presentation_source_image_selection.v1` as the first deterministic source image selection contract. It selects only reusable image candidates from uploaded document assets and uploaded PPTX template media, requires citation/provenance/checksum evidence for every selected image, rejects generated/random/fake/inline/external image candidates fail-closed, and returns typographic fallback bindings when no relevant source image exists. KR-7J does not implement renderer image mapping, source image retrieval UI, generated images, visual QA/scoring, professional layout, GigaChat/runtime changes, Docker/deploy/Postgres changes, or Kimi-level quality claims.

KR-7J validation includes `kw_source_image_selection_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. The next phase remains KR-7K data-backed charts.

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



KR-7L adds `presentation_professional_layout_engine.v1` as the first deterministic professional layout planning layer after template/brand understanding, source-image selection, and data-backed chart binding. It computes slide-size-aware grid boxes, margins, gutters, typography, text fitting, overlap detection, title-clipping prevention, and density/contrast/readability/layout scores. It must keep `no_renderer_runtime_mapping`, native PPTX placement, rendered PNG QA execution, visual QA/scoring runtime, production layout quality claims, UI, GigaChat/runtime, Docker/deploy/Postgres changes, and Kimi-level quality claims out of scope.

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

Implementation note after KR-7G.3:

```text
KR-7G.3 exposes read-only visual grammar catalog and binding validation APIs. It adds /api/v1/presentation-visual-grammar/catalog and /api/v1/presentations/{presentation_id}/visual-grammar so clients can inspect presentation_visual_grammar.v1 block specs and validated presentation_ir_visual_grammar_binding.v1 metadata from the latest public-safe PresentationIR snapshot.
The endpoints explicitly report renderer_runtime_implemented=false and do not implement PPTX rendering, final GigaChat planning runtime, embeddings, web research, generated images, visual QA, quality scoring, or UI runtime.
```

Implementation note after KR-7H.1:

```text
KR-7H.1 renderer worker boundary contract preflight defines presentation_renderer_worker_contract.v1 and presentation_renderer_worker_input.v1 for the future native renderer boundary. The contract models Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle and validates fail-closed input readiness before any renderer runtime exists.
KR-7H.1 explicitly keeps renderer_runtime_implemented=false, artifact_bundle_produced=false, and proof_bundle_produced=false. It does not create production-quality PPTX output, does not start Node/PptxGenJS, does not run LibreOffice, and does not perform visual QA or quality scoring.
```


Implementation note after KR-7H.2:

```text
KR-7H.2 renderer worker dry-run scaffold contract defines presentation_renderer_worker_dry_run.v1 and presentation_renderer_worker_invocation_manifest.v1.
The dry run validates PresentationIR through the KR-7H.1 renderer input boundary, emits a deterministic invocation manifest for the future Node/PptxGenJS worker, and blocks unsupported or prompt-only inputs fail-closed.
KR-7H.2 still produces no production PPTX, no Node/PptxGenJS runtime execution, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.
```

Implementation note after KR-7H.3:

```text
KR-7H.3 renderer worker protocol preflight scaffold defines presentation_renderer_worker_protocol_preflight.v1 and presentation_renderer_worker_protocol_preflight_response.v1.
It adds a deterministic Node-side protocol preflight script that validates KR-7H.2 dry-run reports and invocation manifests at the future worker boundary.
KR-7H.3 still produces no production PPTX, no PptxGenJS rendering, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.
```

Implementation note after KR-7H.4:

```text
KR-7H.4 isolated renderer worker package preflight defines presentation_renderer_worker_package_preflight.v1.
It adds a private renderer_worker package boundary with deterministic npm run protocol:preflight and npm run check scripts, keeping renderer worker package concerns separate from frontend UI package concerns.
KR-7H.4 still has no PptxGenJS dependency, no production PPTX output, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.
```

Implementation note after KR-7H.5:

KR-7H.5 controlled PptxGenJS capability preflight defines `presentation_renderer_worker_pptxgenjs_capability.v1`.
The PptxGenJS dependency is introduced only inside renderer_worker as pinned `pptxgenjs@4.0.1` with an isolated package lock and package-level capability script.
The capability check verifies dependency availability/version and the default export shape for future renderer work, but it does not generate PPTX, map PresentationIR blocks into slides, run LibreOffice, produce proof/artifact bundles, perform visual QA, or claim production-quality output.


Implementation note after KR-7H.6:

KR-7H.6 in-memory PptxGenJS construction preflight defines `presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1`.
The preflight imports the pinned PptxGenJS dependency and constructs a presentation object in memory only, reporting zero slides, `slide_content_added=false`, `pptxgenjs_write_api_called=false`, and `filesystem_output_written=false`.
KR-7H.6 still has no PPTX file output, no PresentationIR mapping, no slide content generation, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.


Implementation note after KR-7H.7:

KR-7H.7 controlled empty PPTX file output smoke defines `presentation_renderer_worker_empty_pptx_output_smoke.v1`. The smoke may write a temporary empty `.pptx` only as local capability evidence, verify non-zero size, and delete the temporary file before returning ready. KR-7H.7 still has no PresentationIR mapping, no user-visible deck content, no persistent artifact, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.


Implementation note after KR-7H.8:

KR-7H.8 controlled static single-slide PPTX output smoke defines `presentation_renderer_worker_static_slide_output_smoke.v1`. The smoke may write a temporary `.pptx` containing exactly one fixed technical smoke slide only as local capability evidence, verify non-zero size, and delete the temporary file before returning ready. KR-7H.8 still has no PresentationIR mapping, no user/evidence content, no user-visible deck content, no persistent artifact, no LibreOffice proof, no artifact/proof bundles, no visual QA, and no quality scoring.

Implementation note after KR-7H.9:

KR-7H.9 minimal PresentationIR mapping temporary PPTX smoke defines `presentation_renderer_worker_minimal_ir_mapping_smoke.v1`. The smoke may map only title/body text from validated renderer input / source-backed dry-run payloads into temporary single-slide and multi-slide `.pptx` files, verify non-zero sizes, and delete all temporary outputs before returning ready. KR-7H.9 still has no persistent PPTX artifact, no LibreOffice proof, no artifact/proof bundles, no visual QA, no chart/table/image/theme/brand mapping, and no production-quality output claim.

### KR-7H.9 minimal PresentationIR mapping + single/multi-slide temporary PPTX smoke

KR-7H.9 introduces `presentation_renderer_worker_minimal_ir_mapping_smoke.v1` after the static single-slide output smoke. It is the first controlled renderer mapping smoke, but it is still not a production renderer.

Scope:

```text
validated renderer input / source-backed dry-run payload;
map only title/body text;
execute single-slide temporary PPTX smoke;
execute multi-slide temporary PPTX smoke;
verify non-zero temporary file sizes;
delete temporary PPTX files and temp directory;
return deterministic JSON report.
```

Non-goals:

```text
no persistent PPTX artifact;
no backend artifact bundle;
no LibreOffice proof;
no proof bundle;
no visual QA/scoring;
no chart/table/image mapping;
no theme/brand/professional layout engine;
no frontend UI/package changes;
no GigaChat/runtime changes;
no production-quality output claim.
```

KR-7H.9 must be validated by `scripts/kw_renderer_worker_minimal_ir_mapping_check.py`, targeted service tests, full runner, Docker smoke, and remote HEAD verification.


Implementation note after KR-7H.10:

KR-7H.10 adds `presentation_renderer_worker_pptx_artifact_bundle.v1` and `presentation_renderer_worker_render_report.v1`. It writes a persistent PPTX artifact and deterministic render report JSON into an explicit controlled renderer-worker output directory using only the previously allowed title/body mapping from validated renderer input / source-backed dry-run payloads. KR-7H.10 still has no LibreOffice PDF/PNG proof, no proof bundle, no visual QA/scoring, no chart/table/image/theme/brand/professional layout mapping, no frontend changes, no GigaChat/runtime changes, and no production-quality or Kimi-level output claim.

### KR-7H.10 persistent PPTX artifact bundle + render report contract

KR-7H.10 is the persistent artifact-bundle step in the consolidated KR-7H plan. It may create a controlled PPTX artifact bundle and render report contract, but it must not run LibreOffice, generate proof images, produce proof bundles, broaden renderer mapping beyond title/body text, or claim production renderer closure. Validation must include exact package self-test, `kw_renderer_worker_pptx_artifact_bundle_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification.


Implementation note after KR-7H.11:

KR-7H.11 adds `presentation_renderer_worker_libreoffice_proof_bundle.v1` on top of the KR-7H.10 controlled persistent PPTX artifact bundle. It uses LibreOffice/`soffice` headless export to produce a real PDF proof and `pdftoppm` to produce real PNG proof files, then writes `kr7h11-proof-bundle.json` with file-size and checksum evidence. It fails closed if LibreOffice/`soffice`, `pdftoppm`, the PDF proof, PNG proofs, or proof-bundle JSON are missing or empty. KR-7H.11 still does not perform visual QA/scoring, does not broaden mapping beyond title/body text, does not map charts/tables/images/theme/brand/professional layout, does not change UI or GigaChat/runtime behavior, and does not claim production-quality/Kimi-level output.

### KR-7H.11 LibreOffice proof bundle smoke contract

KR-7H.11 validation must include exact package self-test through `npm run pptxgenjs:libreoffice-proof-bundle --prefix renderer_worker`, `kw_renderer_worker_libreoffice_proof_bundle_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. The next KR-7H.12 step remains renderer hardening: source-image-only, fail-closed, no fake artifacts; KR-7H.13 remains the KR-7H closure gate.


### KR-7H.12 renderer source-image hardening contract

KR-7H.12 adds `presentation_renderer_worker_source_image_hardening.v1` as a guardrail/checker layer after the LibreOffice proof bundle smoke. It enforces source-image-only renderer input validation and fails closed for generated, fake, fallback, placeholder, random, web, synthetic, inline data URI, base64, or raw-byte image payloads. It also blocks `requires_image=true` slides unless a source image asset/ref is bound. It does not implement source image selection, image mapping, visual QA/scoring, professional layout, UI changes, GigaChat/runtime changes, or production renderer closure. Validation must include `kw_renderer_worker_source_image_hardening_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification.

Implementation note after KR-7H.13:

KR-7H.13 adds `presentation_renderer_worker_kr7h_closure_gate.v1` as the KR-7H closure gate. It verifies that KR-7H.1 through KR-7H.12 renderer-worker foundation contracts are present and covered by project-resident checks, including boundary/dry-run/protocol/package, PptxGenJS capability and smoke layers, minimal title/body mapping, controlled PPTX artifact bundle, LibreOffice PDF/PNG proof bundle, and source-image-only fail-closed hardening.

### KR-7H.13 KR-7H closure gate

KR-7H.13 closes the KR-7H renderer-worker foundation phase only. It must keep `renderer_runtime_implemented=false`, `production_pptx_output_implemented=false`, `production_renderer_closure_implemented=false`, `visual_qa_executed=false`, `visual_quality_score=null`, `kimi_level_quality_claimed=false`, `source_image_selection_implemented=false`, and `image_mapping_implemented=false`. Validation must include `kw_renderer_worker_kr7h_closure_gate_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification. The next phase is KR-7I template and brand understanding.
Implementation note after KR-7K:

KR-7K adds `presentation_data_backed_charts.v1` as a deterministic data-backed chart binding/spec contract after KR-7J source image selection. It accepts only real numeric series from extracted tables, extracted chart data candidates with numeric metadata, or explicitly user-provided numeric data with provenance/data refs. It requires labels, numeric finite values, units or `unknown`, data_ref/provenance_ref, and source identifiers for every bound chart. It fails closed for missing data, fake/generated/random values, non-numeric values, bullet-length charts, and charts without source refs. KR-7K does not implement renderer chart placement, native PPTX chart rendering runtime, visual QA/scoring, UI changes, GigaChat/runtime changes, Docker/deploy/Postgres changes, or Kimi-level claims. Validation must include `kw_data_backed_charts_check.py`, targeted pytest, inventory, `git diff --check`, full runner, Docker smoke, push, and remote HEAD verification.
KR-7L professional layout engine contract phrase anchor: `presentation_professional_layout_engine.v1`, `no_renderer_runtime_mapping`, and `no_production_layout_quality_claim`.

## KR-7M implementation note — Presentation Studio UI contract

KR-7M adds `presentation_studio_ui.v1` as the first API-first Presentation Studio UI contract after KR-7L. It introduces a frontend Presentation Studio surface for slide thumbnails, canvas preview, block inspector, asset provenance tray, deck quality warnings, backend draft persistence, and backend-side export requests.

Scope boundaries:

```text
backend_url_configurable
openapi_client_contract_implemented
backend_side_export_only
no_frontend_side_generation_as_source_of_truth
no_arbitrary_model_selector
no_renderer_runtime_changes
no_gigachat_runtime_changes
no_docker_deploy_changes
no_visual_qa_runtime_execution
no_production_ui_quality_claim
no_kimi_level_quality_claim
```

KR-7M does not implement final generated OpenAPI codegen, production backend studio endpoints, frontend-side deck generation, renderer placement, visual QA/scoring, GigaChat/runtime changes, or Docker/deploy/Postgres changes. Backend APIs remain the source of truth for draft persistence and export.

KR-7M Presentation Studio UI: contract anchor for `presentation_studio_ui.v1`.

### KR-7N implementation note — professional quality evaluator contract

KR-7N adds `presentation_professional_quality_evaluator.v1` and a deterministic `quality_report.json` contract. The quality evaluator scores content, design, coherence, data, assets, and export readiness from existing source-backed reports. `quality_pass=true` is required before any later professional/Kimi-level status may be claimed, but KR-7N itself keeps `kimi_level_quality_claimed=false` and `production_quality_claimed=false`.

Non-goals: `no_visual_qa_runtime_execution`, `no_rendered_png_quality_scoring`, `no_renderer_runtime_changes`, `no_frontend_runtime_changes`, `no_gigachat_runtime_changes`, `no_docker_deploy_postgres_changes`, `no_production_quality_claim`, `no_kimi_level_quality_claim`.

KR-7N professional quality evaluator anchors: `presentation_professional_quality_evaluator.v1`, `quality_report.json`, `no_visual_qa_runtime_execution`, `no_kimi_level_quality_claim`.

## Product-slice re-baseline after KR-7N

KR-7H established renderer-worker foundations. KR-7I through KR-7N established deterministic template, image, data, layout, UI, and quality contracts. These contracts are necessary but not enough for Kimi-like Slides progress unless they are integrated into a vertical workflow.

Effective immediately:

```text
post-KR-7H patches must prefer vertical product slices over isolated contracts;
contract-only work must be labelled phase-entry scaffold or governance repair;
phase closure must identify the artifact/API/UI/report outcome improved by the patch;
limitations must be represented as honest degraded/partial states, not fake success;
KR-7O scenario packs must include integration with PresentationIR, template/layout/data/image availability, provenance, and quality reporting.
```

The next KR-7O plan must include a remediation table for KR-7I through KR-7N and must not close with only scenario-pack schemas/checkers.
