# KR-7H renderer worker package preflight contract

Historical baseline: KR-7H.4 renderer worker package preflight contract.

KR-7H.4 adds an isolated `renderer_worker` package boundary for the future native PPTX renderer worker.

This package boundary is deliberately separate from the frontend UI package. Renderer worker package checks must not require changes to `frontend/package.json`, frontend build scripts, or frontend runtime dependencies.

KR-7H.5 extends that package boundary with a controlled PptxGenJS dependency capability preflight. PptxGenJS is declared only inside the isolated renderer_worker package, pinned to `pptxgenjs@4.0.1`, and used only to verify dependency availability/version for later renderer work.

KR-7H.6 extends that boundary with an in-memory PptxGenJS construction preflight. The in-memory preflight may import PptxGenJS and construct a presentation object in memory to verify the first controlled API-level smoke, but it must not add slide content, map PresentationIR blocks into slides, call write/output APIs, write `.pptx` files, run LibreOffice, or produce artifact/proof bundles.

## Contract identifiers

- `presentation_renderer_worker_package_preflight.v1`
- `presentation_renderer_worker_protocol_preflight.v1`
- `presentation_renderer_worker_protocol_preflight_response.v1`
- `presentation_renderer_worker_pptxgenjs_capability.v1`
- `presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1`

## Required package scripts

- `npm run protocol:preflight --prefix renderer_worker`
- `npm run dependency:capability --prefix renderer_worker`
- `npm run pptxgenjs:in-memory --prefix renderer_worker`
- `npm run check --prefix renderer_worker`

The `check` script confirms package isolation, protocol preflight readiness, and controlled PptxGenJS capability only. It does not generate PPTX, does not map PresentationIR blocks into slides, does not start a long-running worker service, and does not execute LibreOffice.

## Runtime flags

The package contract must keep these claims false:

- `renderer_runtime_implemented=false`
- `production_pptx_output_implemented=false`
- `pptx_generation_executed=false`
- `artifact_bundle_produced=false`
- `proof_bundle_produced=false`
- `slide_content_added=false`
- `pptxgenjs_write_api_called=false`
- `filesystem_output_written=false`

## Dependency boundary

- `renderer_worker/package.json` may declare only the controlled `pptxgenjs@4.0.1` dependency for KR-7H.5.
- `frontend/package.json` must not declare `pptxgenjs` or `kw-studio-renderer-worker` for renderer worker needs.
- `renderer_worker/package-lock.json` must lock the isolated worker dependency tree.
- The dependency capability preflight may resolve/import the package to inspect availability and version, but it must not instantiate a deck for output, add slide content, write `.pptx` files, or execute any proof/export workflow.
- The KR-7H.6 in-memory preflight may construct `new PptxGenJS()` only as an in-memory object smoke. It must report `slide_count=0`, `slide_content_added=false`, `pptxgenjs_write_api_called=false`, and `filesystem_output_written=false`.

## Explicit non-goals

KR-7H.5 does not generate production PPTX, does not map PresentationIR blocks into slides, does not call PptxGenJS output APIs, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, does not perform visual QA, does not change UI, and does not change GigaChat runtime. KR-7H.6 does not write .pptx files, does not map PresentationIR blocks into slides, does not add slide content, does not call PptxGenJS write/output APIs, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, and does not claim production renderer readiness.
