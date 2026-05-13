# Render and Visual QA

Render QA verifies that visual artifacts can be rendered independently and inspected after generation.

## Slides requirements

- Generate native PPTX.
- Render PPTX through an independent renderer when available.
- Count rendered slides.
- Detect empty slides, tiny text, text overflow, and blocking layout defects when supported.
- Store rendered images in the artifact bundle.

## Why independent render matters

A generator preview is not enough. The delivered PPTX must be checked through a separate rendering path so broken OOXML, missing layout data, or renderer-specific failures are caught before delivery.

## Limits

Render QA is a technical quality gate. It does not prove strategic narrative quality, design taste, or human approval.
