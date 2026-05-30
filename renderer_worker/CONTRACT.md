# KR-7H renderer worker package preflight contract

Historical baseline: KR-7H.4 renderer worker package preflight contract.

KR-7H.4 adds an isolated `renderer_worker` package boundary for the future native PPTX renderer worker.

This package boundary is deliberately separate from the frontend UI package. Renderer worker package checks must not require changes to `frontend/package.json`, frontend build scripts, or frontend runtime dependencies.

KR-7H.5 extends that package boundary with a controlled PptxGenJS dependency capability preflight. PptxGenJS is declared only inside the isolated renderer_worker package, pinned to `pptxgenjs@4.0.1`, and used only to verify dependency availability/version for later renderer work.

KR-7H.6 extends that boundary with an in-memory PptxGenJS construction preflight. The in-memory preflight may import PptxGenJS and construct a presentation object in memory to verify the first controlled API-level smoke, but it must not add slide content, map PresentationIR blocks into slides, call write/output APIs, write `.pptx` files, run LibreOffice, or produce artifact/proof bundles.

KR-7H.7 extends that boundary with a controlled empty PPTX file output smoke. The smoke may call PptxGenJS `writeFile` only against an ephemeral temporary file, verify that the temporary `.pptx` exists and has non-zero size, then delete the file and temporary directory before returning ready. The temporary smoke output is not a persisted artifact, not a production deck, not a PresentationIR mapping, and not a proof bundle.

KR-7H.8 extends that boundary with a controlled static single-slide PPTX output smoke. The smoke may add exactly one fixed technical slide with static renderer-worker smoke text, call PptxGenJS `writeFile` only against an ephemeral temporary file, verify that the temporary `.pptx` exists and has non-zero size, then delete the file and temporary directory before returning ready. The fixed technical slide is not user prompt content, not evidence content, not PresentationIR mapping, not a persisted artifact, not a production deck, and not a proof bundle.

KR-7H.9 extends that boundary with minimal PresentationIR mapping plus single-slide and multi-slide temporary PPTX smoke. The smoke may map only `title` and `body` text from validated renderer input / source-backed dry-run payloads, write temporary single-slide and multi-slide `.pptx` files, verify non-zero size, and delete all temporary outputs before returning ready. It does not map charts, tables, images, theme, brand, or professional layout; it does not persist PPTX artifacts, run LibreOffice, create proof bundles, or claim production renderer readiness.

KR-7H.11 extends the KR-7H.10 persistent PPTX artifact bundle path with a controlled LibreOffice + `pdftoppm` proof bundle smoke. It may run LibreOffice headless to export the existing controlled PPTX artifact to PDF, run `pdftoppm` to render PNG proof files, and write `presentation_renderer_worker_libreoffice_proof_bundle.v1`. It must fail closed when LibreOffice, `pdftoppm`, the PDF proof, any PNG proof, or the proof-bundle JSON is absent or empty. It still does not perform visual QA/scoring, map charts/tables/images/theme/brand/professional layout, change UI/frontend/GigaChat runtime, or claim production-quality renderer closure.

KR-7H.12 hardens renderer input guardrails with `presentation_renderer_worker_source_image_hardening.v1`. It keeps image mapping and source-image selection runtime out of scope, but makes renderer input validation fail closed for generated, fake, fallback, placeholder, random, web, synthetic, or inline image payloads. If a slide requires an image, it must be bound to source image refs/assets before a later renderer phase may use it.

## Contract identifiers

- `presentation_renderer_worker_package_preflight.v1`
- `presentation_renderer_worker_protocol_preflight.v1`
- `presentation_renderer_worker_protocol_preflight_response.v1`
- `presentation_renderer_worker_pptxgenjs_capability.v1`
- `presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1`
- `presentation_renderer_worker_empty_pptx_output_smoke.v1`
- `presentation_renderer_worker_static_slide_output_smoke.v1`
- `presentation_renderer_worker_minimal_ir_mapping_smoke.v1`
- `presentation_renderer_worker_pptx_artifact_bundle.v1`
- `presentation_renderer_worker_render_report.v1`
- `presentation_renderer_worker_libreoffice_proof_bundle.v1`
- `presentation_renderer_worker_source_image_hardening.v1`

## Required package scripts

- `npm run protocol:preflight --prefix renderer_worker`
- `npm run dependency:capability --prefix renderer_worker`
- `npm run pptxgenjs:in-memory --prefix renderer_worker`
- `npm run pptxgenjs:empty-output --prefix renderer_worker`
- `npm run pptxgenjs:static-slide --prefix renderer_worker`
- `npm run pptxgenjs:minimal-ir-smoke --prefix renderer_worker`
- `npm run pptxgenjs:artifact-bundle --prefix renderer_worker`
- `npm run pptxgenjs:libreoffice-proof-bundle --prefix renderer_worker`
- `python scripts/kw_renderer_worker_source_image_hardening_check.py --repo-root . --require-ready`
- `npm run check --prefix renderer_worker`

The `check` script confirms package isolation, protocol preflight readiness, controlled PptxGenJS capability, in-memory construction, temporary empty output smoke, temporary static single-slide output smoke, temporary minimal PresentationIR title/body mapping smoke, persistent PPTX artifact bundle, and LibreOffice proof bundle smoke. The KR-7H.12 Python checker confirms source-image-only fail-closed hardening. It does not generate production PPTX, does not perform visual QA/scoring, does not map charts/tables/images or professional layouts, does not start a long-running worker service, and does not use fake/fallback proof renderers as success evidence.

## Runtime flags

The package contract must keep these claims false:

- `renderer_runtime_implemented=false`
- `production_pptx_output_implemented=false`
- `pptx_generation_executed=false`
- `artifact_bundle_produced=true` after KR-7H.10
- `proof_bundle_produced=true` after KR-7H.11 proof-bundle smoke
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
- `minimal_ir_mapping_smoke_implemented=true`
- `title_body_mapping_implemented=true`
- `mapped_fields=title,body`
- `single_slide_smoke_executed=true`
- `multi_slide_smoke_executed=true`
- `temporary_minimal_ir_pptx_written=true`
- `temporary_minimal_ir_pptx_deleted=true`
- `chart_mapping_implemented=false`
- `table_mapping_implemented=false`
- `image_mapping_implemented=false`
- `source_image_hardening_implemented=true`
- `source_images_only_enforced=true`
- `generated_images_allowed=false`
- `fallback_images_allowed=false`
- `fake_artifacts_allowed=false`
- `inline_image_payloads_allowed=false`
- `source_image_selection_implemented=false`

## Dependency boundary

- `renderer_worker/package.json` may declare only the controlled `pptxgenjs@4.0.1` dependency for KR-7H.5.
- `frontend/package.json` must not declare `pptxgenjs` or `kw-studio-renderer-worker` for renderer worker needs.
- `renderer_worker/package-lock.json` must lock the isolated worker dependency tree.
- The dependency capability preflight may resolve/import the package to inspect availability and version, but it must not instantiate a deck for output, add slide content, write `.pptx` files, or execute any proof/export workflow.
- The KR-7H.6 in-memory preflight may construct `new PptxGenJS()` only as an in-memory object smoke. It must report `slide_count=0`, `slide_content_added=false`, `pptxgenjs_write_api_called=false`, and `filesystem_output_written=false`.
- The KR-7H.7 empty output smoke may call `writeFile` only for an ephemeral temporary `.pptx`, must report `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, `temporary_pptx_file_size_nonzero=true`, `persistent_artifact_written=false`, `production_pptx_output_implemented=false`, and `artifact_bundle_produced=false`.
- The KR-7H.8 static slide output smoke may add exactly one fixed technical slide and call `writeFile` only for an ephemeral temporary `.pptx`. It must report `static_slide_count=1`, `static_slide_content_added=true`, `static_slide_uses_user_content=false`, `static_slide_uses_presentation_ir=false`, `temporary_pptx_written=true`, `temporary_pptx_deleted=true`, `temporary_pptx_file_size_nonzero=true`, `persistent_artifact_written=false`, `production_pptx_output_implemented=false`, and `artifact_bundle_produced=false`.
- The KR-7H.9 minimal IR mapping smoke may map only title/body text from validated renderer input. It must run both single-slide and multi-slide temporary PPTX smoke paths, delete all temporary outputs, and report `title_body_mapping_implemented=true`, `presentation_ir_mapping_implemented=true`, `chart_mapping_implemented=false`, `table_mapping_implemented=false`, `image_mapping_implemented=false`, `persistent_artifact_written=false`, `production_pptx_output_implemented=false`, and `artifact_bundle_produced=false`.

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
- `minimal_ir_mapping_smoke_implemented=true`
- `title_body_mapping_implemented=true`
- `mapped_fields=title,body`
- `single_slide_smoke_executed=true`
- `multi_slide_smoke_executed=true`
- `temporary_minimal_ir_pptx_written=true`
- `temporary_minimal_ir_pptx_deleted=true`
- `chart_mapping_implemented=false`
- `table_mapping_implemented=false`
- `image_mapping_implemented=false`
- `source_image_hardening_implemented=true`
- `source_images_only_enforced=true`
- `generated_images_allowed=false`
- `fallback_images_allowed=false`
- `fake_artifacts_allowed=false`
- `inline_image_payloads_allowed=false`
- `source_image_selection_implemented=false`
- `temporary_pptx_file_size_nonzero=true`
- `persistent_artifact_written=false`
- `filesystem_output_written=false`
- `presentation_ir_mapping_implemented=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=true` after KR-7H.10
- `proof_bundle_produced=true` after KR-7H.11 proof-bundle smoke
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
- `minimal_ir_mapping_smoke_implemented=true`
- `title_body_mapping_implemented=true`
- `mapped_fields=title,body`
- `single_slide_smoke_executed=true`
- `multi_slide_smoke_executed=true`
- `temporary_minimal_ir_pptx_written=true`
- `temporary_minimal_ir_pptx_deleted=true`
- `chart_mapping_implemented=false`
- `table_mapping_implemented=false`
- `image_mapping_implemented=false`
- `source_image_hardening_implemented=true`
- `source_images_only_enforced=true`
- `generated_images_allowed=false`
- `fallback_images_allowed=false`
- `fake_artifacts_allowed=false`
- `inline_image_payloads_allowed=false`
- `source_image_selection_implemented=false`
- `persistent_artifact_written=false`
- `filesystem_output_written=false`
- `presentation_ir_mapping_implemented=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=true` after KR-7H.10
- `proof_bundle_produced=true` after KR-7H.11 proof-bundle smoke
- `libreoffice_executed=false`
- `visual_qa_executed=false`

KR-7H.8 still does not map PresentationIR blocks into slides, does not use user prompt content or source evidence content, does not generate a user-visible deck, does not persist a PPTX artifact, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, and does not claim production-quality PPTX output.


## KR-7H.9 minimal PresentationIR mapping temporary PPTX smoke boundary

KR-7H.9 maps only title/body text from validated renderer input / source-backed dry-run payloads. KR-7H.9 may map only `title` and `body` text from validated renderer input / source-backed dry-run payloads. It must execute both single-slide and multi-slide temporary PPTX smoke paths, verify non-zero file sizes, delete the temporary `.pptx` files, remove the temporary directory, and return a deterministic fail-closed JSON report.

Required claims for `presentation_renderer_worker_minimal_ir_mapping_smoke.v1`:

- `minimal_ir_mapping_smoke_implemented=true`
- `mapped_fields=title,body`
- `mapped_block_types=text`
- `single_slide_smoke_executed=true`
- `multi_slide_smoke_executed=true`
- `single_slide_pptx_written=true`
- `single_slide_pptx_deleted=true`
- `multi_slide_pptx_written=true`
- `multi_slide_pptx_deleted=true`
- `temporary_directory_removed=true`
- `title_body_mapping_implemented=true`
- `presentation_ir_mapping_implemented=true`
- `chart_mapping_implemented=false`
- `table_mapping_implemented=false`
- `image_mapping_implemented=false`
- `source_image_hardening_implemented=true`
- `source_images_only_enforced=true`
- `generated_images_allowed=false`
- `fallback_images_allowed=false`
- `fake_artifacts_allowed=false`
- `inline_image_payloads_allowed=false`
- `source_image_selection_implemented=false`
- `theme_mapping_implemented=false`
- `professional_layout_engine_implemented=false`
- `user_prompt_passthrough_allowed=false`
- `persistent_artifact_written=false`
- `filesystem_output_written=false`
- `production_pptx_output_implemented=false`
- `artifact_bundle_produced=true` after KR-7H.10
- `proof_bundle_produced=true` after KR-7H.11 proof-bundle smoke
- `libreoffice_executed=false`
- `visual_qa_executed=false`

KR-7H.9 still does not create production PPTX output, does not persist artifacts, does not run LibreOffice, does not create PDF/PNG proofs, does not write artifact/proof bundles, does not perform visual QA/scoring, does not map charts/tables/images/theme/brand, and does not claim production-quality PPTX output.


## KR-7H.10 persistent PPTX artifact bundle + render report contract

KR-7H.10 introduces `presentation_renderer_worker_pptx_artifact_bundle.v1` and `presentation_renderer_worker_render_report.v1` after the minimal IR mapping temporary smoke. It is the first renderer-worker contract that may write a persistent PPTX artifact, but only inside an explicit controlled renderer-worker output directory.

Required command:

```bash
npm run pptxgenjs:artifact-bundle --prefix renderer_worker
```

The worker may map only title/body text from validated renderer input or source-backed dry-run payloads. It must write `kr7h10-minimal-ir-rendered.pptx` and `kr7h10-render-report.json`, verify non-zero file sizes, and return deterministic metadata.

Required flags and boundaries:

```text
artifact_bundle_schema_version=presentation_renderer_worker_pptx_artifact_bundle.v1
render_report_schema_version=presentation_renderer_worker_render_report.v1
persistent_artifact_written=true
artifact_bundle_produced=true
artifact_bundle_verified=true
render_report_written=true
render_report_deterministic=true
presentation_ir_mapping_implemented=true
title_body_mapping_implemented=true
production_pptx_output_implemented=false
proof_bundle_produced=false
libreoffice_executed=false
visual_qa_executed=false
chart_mapping_implemented=false
table_mapping_implemented=false
image_mapping_implemented=false
professional_layout_engine_implemented=false
```

KR-7H.10 does not run LibreOffice, does not create PDF/PNG proofs, does not write proof bundles, does not perform visual QA or quality scoring, does not map charts/tables/images/theme/brand, does not change frontend package dependencies, and does not claim production-quality or Kimi-level output.


## KR-7H.11 LibreOffice proof bundle smoke

KR-7H.11 introduces `presentation_renderer_worker_libreoffice_proof_bundle.v1` on top of the KR-7H.10 persistent PPTX artifact bundle. The smoke may only use the existing minimal title/body mapped PPTX artifact, LibreOffice headless PDF export, and `pdftoppm` PNG rendering.

Required command:

```bash
npm run pptxgenjs:libreoffice-proof-bundle --prefix renderer_worker
```

Required files in the controlled output directory:

```text
kr7h10-minimal-ir-rendered.pptx
kr7h10-render-report.json
kr7h11-rendered-proof.pdf
kr7h11-png-proof/slide_*.png
kr7h11-proof-bundle.json
```

Required flags and boundaries:

```text
proof_bundle_schema_version=presentation_renderer_worker_libreoffice_proof_bundle.v1
artifact_bundle_schema_version=presentation_renderer_worker_pptx_artifact_bundle.v1
render_report_schema_version=presentation_renderer_worker_render_report.v1
artifact_bundle_produced=true
artifact_bundle_verified=true
proof_bundle_produced=true
proof_bundle_verified=true
libreoffice_required=true
pdftoppm_required=true
libreoffice_executed=true
pdftoppm_executed=true
pdf_proof_written=true
png_proofs_written=true
fake_proof_used=false
fallback_renderer_used=false
python_pptx_proof_used=false
visual_qa_executed=false
visual_quality_score=null
production_pptx_output_implemented=false
chart_mapping_implemented=false
table_mapping_implemented=false
image_mapping_implemented=false
theme_mapping_implemented=false
professional_layout_engine_implemented=false
```

KR-7H.11 must return `blocked` and a non-zero process exit when LibreOffice/`soffice`, `pdftoppm`, the PDF proof, the PNG proofs, or `kr7h11-proof-bundle.json` are missing or empty. Python-pptx, fake images, placeholder PDFs, and fallback renderers are forbidden as success evidence. KR-7H.11 still does not perform visual QA/scoring, does not broaden mapping beyond title/body text, does not close the production renderer, and does not change UI, GigaChat/runtime, Docker/deploy/Postgres behavior, or frontend package dependencies.

## KR-7H.12 source-image hardening boundary

KR-7H.12 is a renderer guardrail layer, not source image selection or image rendering. It introduces `presentation_renderer_worker_source_image_hardening.v1` and validates that renderer input stays source-image-only before later KR-7J/K/L phases add selection/layout behavior. Generated images, fake images, fallback images, placeholder images, random/web/synthetic images, inline data URIs, and raw base64/byte image payloads must fail closed. A slide with `visual_plan.requires_image=true` must have source image refs/assets; otherwise the renderer input is blocked rather than filled with fake artifacts.

KR-7H.12 still keeps `image_mapping_implemented=false`, `source_image_selection_implemented=false`, `visual_qa_executed=false`, `production_pptx_output_implemented=false`, and `renderer_runtime_implemented=false`.
