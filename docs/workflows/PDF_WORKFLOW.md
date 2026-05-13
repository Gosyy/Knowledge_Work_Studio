# PDF Workflow

The PDF workflow ingests PDFs, extracts evidence, and produces source-grounded outputs for reports, slides, or document generation.

## Goals

- Extract text and metadata from PDF files.
- Preserve page-level references.
- Capture tables and images when supported by the configured tools.
- Make PDF evidence reusable by DOCX, Slides, XLSX, and Python workflows.

## Expected artifacts

- `pdf_extraction_report.json`.
- `page_manifest.json`.
- `source_evidence_manifest.json`.
- Optional extracted tables, images, or generated reports.

## Quality checks

- Input PDF exists and opens.
- Extraction status is explicit.
- Page counts are recorded.
- Evidence references include page numbers.
- Unsupported extraction features are reported, not hidden.
