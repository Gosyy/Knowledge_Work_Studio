# S6 - Image/screenshot-to-slide workflow

- status: `controlled_image_screenshot_to_slide_workflow`
- branch: `9_Product_Release_Hardening`
- baseline before S6: `0ce33b74473e8ffdbf6e47f4096da86b66b898eb`
- Kimi-level claimed: `False`

## Purpose

S6 adds the offline-safe workflow contract for turning screenshots, images, and scanned page images into slide-ready structures.

The goal is not cloud vision. The goal is a controlled local-heavy-module boundary that can prepare OCR/layout/region metadata, reconstruct editable PPTX elements where possible, and preserve source image region provenance.

## Required workflow

The S6 image/screenshot-to-slide path is:

1. receive a local image or screenshot input;
2. identify source image ID and frame/page;
3. run local OCR/layout/region detection through the heavy-module boundary;
4. create region records for text, table, chart, diagram, screenshot, and caption areas;
5. create an image-to-slide plan from those regions;
6. select editable reconstruction where possible: text boxes, PPTX tables, charts/data summaries, and shape diagrams;
7. allow raster fallback only as a non-primary path with an explicit reason;
8. register source-to-region and region-to-slide-element provenance;
9. register artifact history and plan snapshot.

## Offline/intranet boundary

S6 does not add cloud vision, hidden public-internet dependency, public template discovery, or browser automation. Local heavy modules can run on Server 2 or an equivalent intranet node, but S6 does not require live Server 2 verification.

## Acceptance

S6 is accepted when:

- `scripts/kw_s6_image_to_slide_workflow_check.py --repo-root . --require-ready --json` reports `ready`;
- the S6 smoke test passes;
- production readiness `--checks-only` passes;
- full runner and Docker smoke pass after commit and push.

## Non-goals

S6 does not add public API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, hidden internet use, Kimi-level claims, or Server 3 `local_intranet` proof claims.
