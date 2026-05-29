# KR-7H renderer worker package preflight contract

Historical baseline: KR-7H.4 renderer worker package preflight contract.

KR-7H.4 adds an isolated `renderer_worker` package boundary for the future native PPTX renderer worker.

This package boundary is deliberately separate from the frontend UI package. Renderer worker package checks must not require changes to `frontend/package.json`, frontend build scripts, or frontend runtime dependencies.

KR-7H.5 extends that package boundary with a controlled PptxGenJS dependency capability preflight. PptxGenJS is declared only inside the isolated renderer_worker package, pinned to `pptxgenjs@4.0.1`, and used only to verify dependency availability/version for later renderer work.

KR-7H.6 extends that boundary with an in-memory PptxGenJS construction preflight. The in-memory preflight may import PptxGenJS and construct a presentation object in memory to verify the first controlled API-level smoke, but it must not add slide content, map PresentationIR blocks into slides, call write/output APIs, write `.pptx` files, run LibreOffice, or produce artifact/proof bundles.

KR-7H.7 extends that boundary with a controlled empty PPTX file output smoke. The smoke may call PptxGenJS `writeFile` only against an ephemeral temporary file, verify that the temporary `.pptx` exists and has non-zero size, then delete the file and temporary directory before returning ready. The temporary smoke output is not a persisted artifact, not a production deck, not a PresentationIR mapping, and not a proof bundle.

KR-7H.8 extends that boundary with a controlled static single-slide PPTX output smoke. The smoke may add exactly one fixed technical slide with static renderer-worker smoke text, call PptxGenJS `writeFile` only against an ephemeral temporary file, verify that the temporary `.pptx` exists and has non-zero size, then delete the file and temporary directory before returning ready. The fixed technical slide is not user prompt content, not evidence content, not PresentationIR mapping, not a persisted artifact, not a production deck, and not a proof bundle.

## Contract identifiers

- `presentation_renderer_worker_package_preflight.v1`
- `presentation_renderer_worker_protocol_preflight.v1`
- `presentation_renderer_worker_protocol_preflight_response.v1`
- `presentation_renderer_worker_pptxgenjs_capability.v1`
- `presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1`
- `presentation_renderer_worker_empty_pptx_output_smoke.v1`
- `presentation_renderer_worker_static_slide_output_smoke.v1`

## Required package scripts

- `npm run protocol:preflight --prefix renderer_worker`
- `npm run dependency:capability --prefix renderer_worker`
- `npm run pptxgenjs:in-memory --prefix renderer_worker`
- `npm run pptxgenjs:empty-output --prefix renderer_worker`
- `npm run pptxgenjs:static-slide --prefix renderer_worker`
- `npm run check --prefix renderer_worker`

The `check` script confirms package isolation, protocol preflight readiness, controlled PptxGenJS capability, in-memory construction, temporary empty output smoke, and temporary static single-slide output smoke only. It does not generate production PPTX, does not map PresentationIR blocks into slides, does not start a long-running worker service, and does not execute LibreOffice.

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
- `persistent_artifact_written=false`
- `temporary_pptx_written=true`
- `temporary_pptx_deleted=true`
- `static_slide_count=1`
- `static_slide_content_added=true`
- `static_slide_uses_user_content=false`
- `static_slide_uses_presentation_ir=false`

## Dependency boundary

- `renderer_worker/package.json` may declare only the controlled `pptxgenjs@4.0.1` dependency for KR-7H.5.
- `frontend/package.json` must not declare `pptxgenjs` or `kw-studio-renderer-worker` for renderer worker needs.
- `renderer_worker/package-lock.json` must lock the isolated worker dependency tree.
- The dependency capability preflight may resolve/import the package to inspect availability and version, but it must not instantiate a deck for output, add slide content, write `.pptx` files, or execute any proof/export workflow.
- The KR-7H.6 in-memory preflight may construct `new PptxGenJS()` only as an in-memory object smoke. It must report `slide_count=0`, `slide_content_added=false`, `pptxgenjs_write_api_called=false`, and `filesystem_output_written=false`.
- The KR-7H.7 empty output smoke may call `writeFile` only for an ephemeral temporary `.pptx`, must report `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, `temporary_pptx_file_size_nonzero=true`, `persistent_artifact_written=false`, `production_pptx_output_implemented=false`, and `artifact_bundle_produced=false`.
- The KR-7H.8 static slide output smoke may add exactly one fixed technical slide and call `writeFile` only for an ephemeral temporary `.pptx`. It must report `static_slide_count=1`, `static_slide_content_added=true`, `static_slide_uses_user_content=false`, `static_slide_uses_presentation_ir=false`, `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, `temporary_pptx_file_size_nonzero=true`, `persistent_artifact_written=false`, `production_pptx_output_implemented=false`, and `artifact_bundle_produced=false`.

## Explicit non-goals

KR-7H.5 does not generate production PPTX, does not map PresentationIR blocks into slides, does not call PptxGenJS output APIs, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, does not perform visual QA, does not change UI, and does not change GigaChat runtime. KR-7H.6 does not write .pptx files, does not map PresentationIR blocks into slides, does not add slide content, does not call PptxGenJS write/output APIs, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, and does not claim production renderer readiness.


## KR-7H.7 temporary empty output smoke boundary

KR-7H.7 may write a temporary empty `.pptx` only as local renderer worker capability evidence. The script must create the file in an ephemeral temporary directory, verify non-zero size, delete the temporary `.pptx`, remove the temporary directory, and return a deterministic fail-closed JSON report.

Required claims for `presentation_renderer_worker_empty_pptx_output_smoke.v1`:

- `temporary_pptx_written=true`
- `temporary_pptx_deleted=true`
- `static_slide_count=1`
- `static_slide_content_added=true`
- `static_slide_uses_user_content=false`
- `static_slide_uses_presentation_ir=false`
- `temporary_pptx_file_size_nonzero=true`
- `persistent_artifact_written=false`
- `filesystem_output_written=false`
- `presentation_ir_mapping_implemented=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=false`
- `proof_bundle_produced=false`
- `libreoffice_executed=false`
- `visual_qa_executed=false`

KR-7H.7 still does not map PresentationIR blocks into slides, does not generate user-visible deck content, does not persist a PPTX artifact, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, and does not claim production-quality PPTX output.


## KR-7H.8 temporary static single-slide output smoke boundary

KR-7H.8 may write a temporary `.pptx` containing exactly one fixed technical smoke slide only as local renderer worker capability evidence. The script must create the file in an ephemeral temporary directory, verify non-zero size, delete the temporary `.pptx`, remove the temporary directory, and return a deterministic fail-closed JSON report.

Required claims for `presentation_renderer_worker_static_slide_output_smoke.v1`:

- `temporary_pptx_written=true`
- `temporary_pptx_deleted=true`
- `temporary_pptx_file_size_nonzero=true`
- `static_slide_count=1`
- `static_slide_content_added=true`
- `static_slide_uses_user_content=false`
- `static_slide_uses_presentation_ir=false`
- `persistent_artifact_written=false`
- `filesystem_output_written=false`
- `presentation_ir_mapping_implemented=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=false`
- `proof_bundle_produced=false`
- `libreoffice_executed=false`
- `visual_qa_executed=false`

KR-7H.8 still does not map PresentationIR blocks into slides, does not use user prompt content or source evidence content, does not generate a user-visible deck, does not persist a PPTX artifact, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, and does not claim production-quality PPTX output.
