# KW Studio Product Vision

KW Studio is an offline/intranet, artifact-first knowledge-work studio. It turns user files, data, browser evidence, and natural-language instructions into downloadable, validated, and auditable work products.

The product is not a generic chat interface. The product is a controlled workflow system for professional knowledge work:

- DOCX document drafting, editing, rewriting, and review packets.
- PDF ingestion, extraction, summarization, evidence capture, and report generation.
- XLSX/Excel analysis, workbook inspection, formula validation, chart/table extraction, and workbook outputs.
- Slides generation, outline-first planning, native PPTX output, independent render QA, and source-grounded review packets.
- Python analysis for data, tables, charts, diagnostics, and reproducible computation.
- Browser-assisted workflows for intranet/public-page evidence capture with screenshots, source manifests, and task provenance.

## Product principles

1. **Artifact first**: every important workflow produces files, manifests, and quality reports, not just chat text.
2. **Offline/intranet first**: production workflows must operate without public internet access unless an operator explicitly enables a controlled connector.
3. **Provenance first**: generated claims, slides, reports, charts, and workbook changes should be traceable to source files, browser evidence, or explicit user input.
4. **Operator gated**: release, restore, backup, destructive edits, external calls, and security changes require visible checks and reviewable logs.
5. **Portable by default**: the project must run from any checkout path and on any supported machine. Active code, tests, and docs must not depend on local profile names, `Downloads`, branch names, or commit hashes.
6. **Local LLM first**: the default production route is the local GigaChat endpoint on the intranet. LiteLLM-compatible gateway and other providers are optional adapters, not the core product identity.

## What KW Studio should feel like

A user should be able to upload source material, choose a workflow, inspect or approve a plan, run generation, see progress, download artifacts, review provenance, and retry or restore without losing context.

The strongest version of the product is a senior-engineer-grade workstation for document, data, presentation, and evidence workflows. It should combine deterministic backend tools with LLM planning and explanation, while keeping validation and artifact integrity in the backend.
