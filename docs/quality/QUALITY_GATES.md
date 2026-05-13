# Quality Gates

Quality gates define when KW Studio can trust an artifact enough to show, download, or release it.

## Common gates

- Artifact exists and is non-empty.
- Artifact opens with the expected parser or renderer.
- Bundle manifest is present.
- Quality report is present.
- Provenance manifest is present for source-grounded workflows.
- Review packet is present for human review workflows.
- Logs are archived and secrets are redacted.

## Workflow-specific gates

- DOCX: OOXML opens and expected sections exist.
- PDF: page count and extraction status are recorded.
- XLSX: workbook opens, sheets are inventoried, formulas are reported, generated workbook validates.
- Slides: PPTX opens, independent render works, visual QA passes thresholds.
- Python analysis: inputs, outputs, and computation summary are recorded.
- Browser evidence: screenshots and source locators are present.

## Non-goals

A passing quality gate does not automatically mean the output is expert-level, Kimi-level, legally approved, financially approved, or human-approved. Gates prove specific technical and provenance properties.

Important: passing KW Studio quality gates does not prove Kimi-level quality, does not claim selected workflow parity, and does not replace human review. Quality gates prove specific technical, provenance, render, and artifact properties only.

