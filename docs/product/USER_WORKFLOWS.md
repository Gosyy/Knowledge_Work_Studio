# User Workflows

KW Studio supports six mandatory workflow families. Each workflow must have a plan, artifacts, validation, provenance, and a reviewable result.

## 1. DOCX workflow

Typical tasks:

- Draft a document from notes or source files.
- Rewrite a document while preserving structure.
- Compare source and generated versions.
- Produce a review packet with changes, assumptions, and citations.

Expected outputs:

- Edited or generated `.docx`.
- Change summary.
- Source evidence manifest.
- Validation report.

## 2. PDF workflow

Typical tasks:

- Ingest PDF files.
- Extract text, tables, and page-level evidence.
- Summarize or transform content into reports.
- Use PDF evidence as source material for slides or DOCX.

Expected outputs:

- Extraction report.
- Page/source manifest.
- Derived report artifacts.
- Evidence snippets with page references.

## 3. XLSX/Excel workflow

Typical tasks:

- Inspect workbooks and sheets.
- Detect tables, formulas, named ranges, and chart inputs.
- Validate formulas and workbook integrity.
- Create analysis reports, cleaned workbooks, and chart/table artifacts.
- Feed Excel-derived tables/charts into Slides.

Expected outputs:

- Workbook manifest.
- Formula inventory and validation report.
- Table previews.
- Optional generated workbook.
- Source-to-chart/table provenance.

## 4. Slides workflow

Typical tasks:

- Generate a presentation from a prompt and source bundle.
- Produce and edit an outline before generation.
- Generate native PPTX with citations and source evidence.
- Independently render PPTX and run visual QA.
- Revise deck from a saved plan.

Expected outputs:

- `.pptx` deck.
- Rendered slide previews.
- Independent render output.
- Geometry/visual QA reports.
- Citation and source evidence manifests.
- Review packet over actual rendered deck.

## 5. Python analysis workflow

Typical tasks:

- Analyze CSV/XLSX/PDF-extracted data.
- Produce tables, plots, and diagnostics.
- Run reproducible calculations.
- Package results as artifacts for documents and slides.

Expected outputs:

- Analysis report.
- Data/profile manifest.
- Generated tables and charts.
- Code execution summary and validation output.

## 6. Browser-assisted evidence workflow

Typical tasks:

- Capture evidence from internal or public web pages.
- Collect screenshots, URLs, timestamps, and notes.
- Use browser evidence as source material for reports or slides.

Expected outputs:

- Browser evidence manifest.
- Screenshot artifacts.
- Page text or structured extracts when allowed.
- Source references usable by downstream workflows.
