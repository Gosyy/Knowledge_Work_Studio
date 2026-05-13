# Browser-assisted Evidence Workflow

The browser-assisted evidence workflow captures web or intranet evidence for downstream documents, spreadsheets, reports, and slides.

## Goals

- Capture page-level evidence with URLs, timestamps, titles, and screenshots.
- Use browser evidence as source material in generated artifacts.
- Keep evidence reviewable and reproducible within operator constraints.

## Expected artifacts

- `browser_evidence_manifest.json`.
- Screenshot files.
- Extracted snippets when allowed.
- Source references for downstream workflows.

## Quality checks

- Each evidence item has a source URL or internal locator.
- Screenshots are saved and referenced relatively.
- Capture time is recorded.
- Browser evidence is not treated as verified truth without review.
