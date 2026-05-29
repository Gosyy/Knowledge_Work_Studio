# KR-7H.4 renderer worker package preflight contract

KR-7H.4 adds an isolated `renderer_worker` package boundary for the future native PPTX renderer worker.

This package boundary is deliberately separate from the frontend UI package. Renderer worker package checks must not require changes to `frontend/package.json`, frontend build scripts, or frontend runtime dependencies.

## Contract identifiers

- `presentation_renderer_worker_package_preflight.v1`
- `presentation_renderer_worker_protocol_preflight.v1`
- `presentation_renderer_worker_protocol_preflight_response.v1`

## Required package scripts

- `npm run protocol:preflight --prefix renderer_worker`
- `npm run check --prefix renderer_worker`

The `check` script confirms package isolation and protocol preflight readiness only. It does not generate PPTX, does not start a long-running worker service, and does not execute LibreOffice.

## Runtime flags

The package contract must keep these claims false:

- `renderer_runtime_implemented=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=false`
- `proof_bundle_produced=false`

## Explicit non-goals

KR-7H.4 does not add a PptxGenJS dependency, does not generate production PPTX, does not map PresentationIR blocks into slides, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, does not perform visual QA, does not change UI, and does not change GigaChat runtime.
