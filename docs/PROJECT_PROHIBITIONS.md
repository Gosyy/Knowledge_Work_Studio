# Project Prohibitions

## Purpose

This document lists shortcuts and failure modes that are forbidden in KW Studio development. It is intentionally explicit so future assistants cannot silently replace product work with weaker behavior.

## Patch process prohibitions

It is forbidden to:

```text
issue code patches without a verified local full-history checkout;
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
