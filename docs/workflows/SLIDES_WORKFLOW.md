# Slides Workflow

The Slides workflow creates source-grounded, editable PowerPoint decks.

## Goals

- Start from prompt, uploaded documents, spreadsheets, browser evidence, or templates.
- Produce an outline before full deck generation.
- Generate native PPTX artifacts.
- Render PPTX independently and validate the render output.
- Produce citations, source evidence, and a review packet over the actual deck.

## Expected artifacts

- `deck.pptx`.
- Rendered preview images.
- Independent render images.
- `geometry_report.json`.
- `visual_qa_report.json`.
- `citation_manifest.json`.
- `source_evidence_manifest.json`.
- `review_packet.json`.

## Quality checks

- PPTX exists and is valid OOXML.
- Slide count matches the plan.
- Independent render produces the expected number of images.
- Empty slides, tiny text, and text overflow are reported.
- Major claims have source evidence when generated from source material.

## Modes

- **Adaptive mode**: the renderer chooses layout and visual structure.
- **Template mode**: the renderer follows a selected or uploaded PPTX template.

Both modes must produce downloadable PPTX and validation artifacts.
