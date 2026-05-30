# Project Prohibitions

## Purpose

This document lists shortcuts and failure modes that are forbidden in KW Studio development. It is intentionally explicit so future assistants cannot silently replace product work with weaker behavior.

## Patch process prohibitions

It is forbidden to:

```text
issue code patches without a verified local full-history checkout;
issue patches or repair packages that were not applied and targeted-tested on the verified local checkout that matches the intended base or dirty-tree state;
treat `git apply --check` alone as sufficient local patch validation;
issue repair runners from GitHub snippets alone;
allow fake/noop providers in development runtime;
assume a clean checkout without checking branch, HEAD and dirty tree;
pull over unknown dirty state;
run project validation through system Python when `.venv` is available;
claim ACCEPT without targeted checks, full runner, Docker smoke, log review, commit, push and remote verification;
weaken tests to hide a product failure;
make brittle text-anchor edits without proving exact pre-state first;
add a new checker, runner, or smoke test without updating `scripts/kw_test_inventory.py` classification rules when required;
use documentation-only patches to claim runtime behavior changed;
make API-first mutation/render/export/quality endpoints look successful before their runtime implementation exists;
persist PresentationIR-compatible payloads without explicit schema_version and validation;
expose PresentationIR payloads through API-first endpoints without version metadata and secret-safe sanitization;
claim source ingestion/extraction is implemented when a patch only adds source attachment/read metadata;
claim PDF/OCR extraction readiness when the extractor returned unsupported;
expose operator absolute storage paths in SourceAssetRegistry manifests;
persist fake source asset bytes, fake checksums, or raw content_bytes in public ingestion report JSON;
claim KR-7E evidence retrieval from KR-7D.3 structure metadata or chart candidates;
claim dependency-backed extraction fidelity without dependency status metadata;
claim research-backed evidence for prompt-only decks;
claim embeddings or PostgreSQL FTS runtime from KR-7E.1 lexical index foundation;
claim web research or autonomous browsing evidence from offline evidence index results;
claim a supported claim when required claim terms are missing from local evidence sections;
claim evidence index persistence is a planner or render runtime;
expose operator absolute paths from persisted offline evidence index manifests;
claim final GigaChat PresentationIR planning runtime from KR-7F.1;
claim prompt-only degraded planner drafts are source-backed;
claim KR-7F.1 planner output has been rendered, exported, visually QA checked, or approved;
claim evidence-aware slide outline planning is final GigaChat planning runtime;
claim unsupported slide outlines are source-backed;
claim blocked planner results are persistable PresentationIR snapshots;
claim KR-7G.1 renders PPTX or native visuals;
accept native_chart visual grammar blocks without real numeric source data and source data refs;
claim visual grammar validators prove renderer output quality.
```


## KR-7H.9 renderer worker minimal PresentationIR mapping smoke prohibitions

It is forbidden to:

```text
claim KR-7H.9 creates production PPTX output;
claim KR-7H.9 persists PPTX artifacts;
claim KR-7H.9 produces artifact/proof bundles;
claim KR-7H.9 runs LibreOffice;
claim KR-7H.9 performs visual QA or quality scoring;
claim KR-7H.9 maps charts, tables, images, theme, brand, or professional layouts;
claim KR-7H.9 allows arbitrary user prompt passthrough into renderer output;
claim KR-7H.9 temporary mapping smoke responses are rendered deck artifacts;
change frontend package/dependency policy for renderer worker needs during KR-7H.9;
run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.9.
```

```text
KR-7H.9 may map only title/body text from validated renderer input or source-backed dry-run payloads into temporary single-slide and multi-slide PPTX smoke files. All temporary files must be deleted before returning ready.
```



## KR-7H.10 renderer worker persistent PPTX artifact bundle prohibitions

During KR-7H.10 it is forbidden to:

```text
claim KR-7H.10 creates production-quality PPTX output;
claim KR-7H.10 runs LibreOffice or creates PDF/PNG proofs;
claim KR-7H.10 produces proof bundles;
claim KR-7H.10 performs visual QA or quality scoring;
claim KR-7H.10 maps charts, tables, images, theme, brand, or professional layouts;
use arbitrary user prompt passthrough into renderer output;
change frontend package/dependency policy for renderer worker needs during KR-7H.10;
change GigaChat/runtime behavior as part of KR-7H.10;
run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.10.
```

```text
KR-7H.10 may write a persistent PPTX artifact only in an explicit controlled renderer-worker output directory and must write a deterministic render report JSON beside it. This is an artifact bundle contract step, not LibreOffice proof, visual QA, or production-quality renderer closure.


## KR-7H.11 renderer worker LibreOffice proof bundle prohibitions

During KR-7H.11 it is forbidden to:

```text
claim KR-7H.11 closes the production renderer;
claim KR-7H.11 performs visual QA, quality scoring, or human review;
claim KR-7H.11 maps charts, tables, images, theme, brand, or professional layouts;
claim KR-7H.11 uses any proof renderer other than LibreOffice PDF export plus pdftoppm PNG rendering;
use python-pptx, generated placeholder images, placeholder PDFs, or fake files as successful proof evidence;
treat missing LibreOffice/soffice, missing pdftoppm, missing PDF, missing PNGs, or missing proof-bundle JSON as success;
change frontend package/dependency policy, UI, GigaChat/runtime, Docker/deploy/Postgres behavior, or run npm audit fix as part of KR-7H.11.
```

KR-7H.11 may create `presentation_renderer_worker_libreoffice_proof_bundle.v1` only from the existing controlled KR-7H.10 PPTX artifact path. It must fail closed when proof dependencies or proof files are unavailable, and it must keep `visual_qa_executed=false`, `visual_quality_score=null`, `production_pptx_output_implemented=false`, and all chart/table/image/theme/pro-layout mapping flags false.
```

## Runtime and deploy prohibitions

It is forbidden to:

```text
weaken production/offline guardrails to make tests pass;
use manual APP_ENV=development as a public GigaChat test workaround;
claim public internet GigaChat tests prove offline/intranet readiness;
use fake/noop LLM providers outside app_env=test automated test doubles;
present Ollama/local-small-LLM endpoints as an active product fallback, provider, topology endpoint, or UI/runtime option;
regenerate deploy env with a new POSTGRES_PASSWORD and recommend container-only cleanup while preserving the old Postgres metadata volume;
delete artifact/storage volumes as a side effect of metadata credential repair;
print Authorization Keys, access tokens, GigaChat secrets, POSTGRES_PASSWORD, `.env.deploy`, or raw LLM responses in logs.
```

## Artifact and workflow prohibitions

It is forbidden to:

```text
silently replace failed LLM generation with fallback content and call it success;
leave original template text in a full-rewrite presentation mode unless the block is explicitly locked;
claim all text blocks were rewritten without a coverage report;
use fallback text as the normal answer when the task requires LLM-generated content;
create fake charts without real data binding;
use generated images in professional Slides paths where the roadmap requires source-backed images only;
put fake size/hash metadata into artifact manifests;
put fake self-reference metadata into artifact_manifest.json instead of explicit self_reference semantics;
claim complete Excel feature coverage without accepted evidence;
claim full PowerPoint template understanding without accepted evidence;
claim Kimi-level quality without quality gates and evidence.
```

## Documentation prohibitions

It is forbidden to:

```text
leave stale “current phase” text that contradicts actual branch state;
copy long policy blocks into multiple docs instead of linking to the authoritative document;
add product docs under docs/codex;
make active product tests depend on raw historical commit SHAs;
hardcode operator machine paths in product code, reusable tests, Dockerfiles, or product docs;
move or delete docs/codex without controlled cleanup and replacement coverage;
introduce unsupported claims or spelling drift in docs, CLI help, comments, or user-facing messages.
```

claim blocked planner results are persistable PresentationIR snapshots.
claim visual grammar blocks are source-backed when planner output has no evidence bindings.

claim visual grammar catalog/read APIs render PPTX or generate visual output.
claim KR-7H.1 renders production-quality PPTX.
claim artifact/proof bundle is produced by KR-7H.1.
start Node/PptxGenJS or LibreOffice runtime from KR-7H.1.

claim KR-7H.2 generates production PPTX.
claim KR-7H.2 starts Node/PptxGenJS or LibreOffice runtime.
claim KR-7H.2 produces artifact/proof bundles.
claim KR-7H.2 dry-run invocation manifests are rendered deck artifacts.

claim KR-7H.3 generates PPTX.
claim KR-7H.3 imports or executes PptxGenJS.
claim KR-7H.3 starts a production renderer worker.
claim KR-7H.3 runs LibreOffice.
claim KR-7H.3 produces artifact/proof bundles.
claim KR-7H.3 protocol preflight responses are rendered deck artifacts.

claim KR-7H.4 generates PPTX.
claim KR-7H.4 adds or executes PptxGenJS.
claim KR-7H.4 starts a production renderer worker service.
claim KR-7H.4 runs LibreOffice.
claim KR-7H.4 produces artifact/proof bundles.
claim KR-7H.4 package preflight responses are rendered deck artifacts.
change frontend package/dependency policy for renderer worker needs during KR-7H.4.

## KR-7H.5 renderer worker dependency capability prohibitions

Do not:

- claim KR-7H.5 generates PPTX;
- claim KR-7H.5 maps PresentationIR blocks into slides;
- claim KR-7H.5 calls PptxGenJS output/write APIs;
- claim KR-7H.5 starts a production renderer worker service;
- claim KR-7H.5 runs LibreOffice;
- claim KR-7H.5 produces artifact/proof bundles;
- claim KR-7H.5 dependency capability preflight responses are rendered deck artifacts;
- change frontend package/dependency policy for renderer worker needs during KR-7H.5;
- run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.5.


## KR-7H.6 renderer worker in-memory PptxGenJS prohibitions

Do not:

- claim KR-7H.6 writes PPTX files;
- claim KR-7H.6 maps PresentationIR blocks into slides;
- claim KR-7H.6 adds slide content;
- claim KR-7H.6 calls PptxGenJS write/output APIs;
- claim KR-7H.6 starts a production renderer worker service;
- claim KR-7H.6 runs LibreOffice;
- claim KR-7H.6 produces artifact/proof bundles;
- claim KR-7H.6 in-memory preflight responses are rendered deck artifacts;
- change frontend package/dependency policy for renderer worker needs during KR-7H.6;
- run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.6.


## KR-7H.7 renderer worker empty PPTX output smoke prohibitions

Do not:

- claim KR-7H.7 creates production PPTX output;
- claim KR-7H.7 maps PresentationIR blocks into slides;
- claim KR-7H.7 generates user-visible deck content;
- claim KR-7H.7 persists PPTX artifacts;
- claim KR-7H.7 runs LibreOffice;
- claim KR-7H.7 produces artifact/proof bundles;
- claim KR-7H.7 temporary empty output smoke responses are rendered deck artifacts;
- change frontend package/dependency policy for renderer worker needs during KR-7H.7;
- run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.7.


## KR-7H.8 renderer worker static single-slide PPTX output smoke prohibitions

Do not:

- claim KR-7H.8 creates production PPTX output;
- claim KR-7H.8 maps PresentationIR blocks into slides;
- claim KR-7H.8 uses user prompt or evidence content;
- claim KR-7H.8 generates user-visible deck content;
- claim KR-7H.8 persists PPTX artifacts;
- claim KR-7H.8 runs LibreOffice;
- claim KR-7H.8 produces artifact/proof bundles;
- claim KR-7H.8 temporary static-slide smoke responses are rendered deck artifacts;
- change frontend package/dependency policy for renderer worker needs during KR-7H.8;
- run npm audit fix or unrelated dependency/security cleanup as part of KR-7H.8.

## KR-7H.12 renderer source-image hardening prohibitions

Do not claim KR-7H.12 implements source image selection, image mapping, visual QA/scoring, professional layout, or production renderer closure. Do not treat generated, fake, fallback, placeholder, random, web, synthetic, inline data URI, base64, or raw-byte image payloads as valid renderer assets. If a slide requires an image and no source image asset/ref is bound, renderer input must fail closed instead of inventing or substituting an image.
