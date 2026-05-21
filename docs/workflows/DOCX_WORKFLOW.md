# DOCX Workflow

The DOCX workflow creates, edits, rewrites, or reviews Microsoft Word documents.

## Goals

- Preserve document structure when editing existing DOCX files.
- Generate reviewable documents from source material.
- Produce a change summary and evidence manifest.
- Validate the generated DOCX before delivery.

## Expected artifacts

- `document.docx` or edited output file.
- `docx_manifest.json`.
- `docx_quality_report.json`.
- `source_evidence_manifest.json`.
- `review_packet.json` or Markdown equivalent.

## Quality checks

- File exists and is non-empty.
- OOXML container opens.
- Required sections are present.
- Source-grounded claims have evidence references when the workflow is source-based.
- No absolute local paths are embedded in manifests.
