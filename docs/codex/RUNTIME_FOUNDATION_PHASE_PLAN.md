# KW Studio Runtime Foundation Phase Plan

## Purpose

Runtime Foundation is the first implementation phase after the accepted R/S
checkpoint on `6_Stage_R`.

It converts the accepted operator foundation and S-phase workflow contracts into
practical offline/intranet runtime value while preserving the architecture
identity of KW Studio.

## Branch policy

- base checkpoint branch: `6_Stage_R`
- base checkpoint commit: `d034314`
- Runtime Foundation branch: `7_Runtime_Foundation`
- `6_Stage_R` remains the accepted R/S checkpoint
- do not rewrite `6_Stage_R` history
- do not force-push unless explicitly instructed by the project owner
- do not create `S11` for this phase

## Non-negotiable architecture identity

KW Studio v1 remains:

- modular monolith;
- offline/intranet first;
- artifact-first;
- provenance-first;
- operator-gated;
- direct local GigaChat-first for production LLM use.

Do not turn the project into:

- a microservice platform;
- a cloud-first framework;
- a general autonomous browser-agent product;
- a general app builder;
- a broad file-format zoo.

## Infrastructure and LLM direction

Server 1 runs KW Studio backend/frontend, Postgres, artifact storage, and
workflows.

Server 2 is optional infrastructure for a LiteLLM-compatible gateway, heavy
runtime modules, embeddings, OCR, rerank, or dev/fallback local model work.

Server 3 runs the local GigaChat runtime and remains the default production LLM
path through an internal `ip:port` endpoint.

LiteLLM must remain optional. It must not replace local GigaChat and must not
silently override the direct GigaChat path.

Ollama/local models remain optional dev/fallback backends, not the default
production backend.

## RF order

### RF0 — Runtime Foundation checkpoint and repository hygiene

Scope:

- create the Runtime Foundation phase plan;
- create branch policy for `7_Runtime_Foundation`;
- keep the accepted R/S mapping intact;
- remove clearly obsolete bootstrap/start-here documents and redundant
  `.gitkeep` placeholders;
- do not change backend, frontend, runtime code, tests, workflows, or gates.

RF0 is accepted only when:

- the working tree is clean before the patch;
- diff scope is docs/hygiene-only;
- `git diff --check` passes;
- production readiness `--checks-only` passes;
- a functional commit and a separate verdict commit are pushed.

### RF1.1 — Offline dependency inventory and reproducibility policy checkpoint

Status: in progress in this patch; accepted only after the functional commit, targeted checks, production readiness gate wiring, and a separate `RF1.1 verdict: ACCEPT` commit.

Scope:
- create the canonical offline dependency reproducibility policy;
- inventory Python, frontend npm, Docker image, Compose, and browser/E2E dependency surfaces;
- add a no-network inventory check that reports current reproducibility gaps without changing runtime behavior;
- wire the inventory check into production readiness gates;
- keep RF1.1 documentation/check-only, with no Docker build rewrite and no dependency upgrades.

Non-goals:
- do not resolve npm audit findings in RF1.1;
- do not change package versions in RF1.1;
- do not introduce package mirrors or registries in RF1.1;
- do not change slides, document, browser, or LLM runtime behavior in RF1.1.

Acceptance:
- `python3 scripts/kw_offline_dependency_inventory_check.py --repo-root . --require-ready` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_offline_dependency_inventory.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.1 runner passes before the verdict commit is considered accepted.

### RF1 — Offline dependency and Docker reproducibility hardening

Goal: make KW Studio deployment predictable in offline/intranet environments.

Scope candidates:

- Python dependency inventory;
- frontend npm dependency inventory;
- Docker image/build dependency inventory;
- local wheelhouse/npm-cache or local registry guidance;
- offline bootstrap documentation;
- reproducible Docker build/check-only policy;
- checks that fail clearly when a workflow accidentally requires internet.

Non-goals:

- do not redesign the runtime architecture;
- do not add cloud package services as production dependencies;
- do not change slides or document runtime behavior except where strictly
  needed for offline dependency validation.

### RF1.2 — Offline bootstrap bundle policy and cache strategy

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.2 full runner, and a separate `RF1.2 verdict: ACCEPT` commit.

Scope:
- define explicit offline/bootstrap modes: check-only, skip-build runtime smoke, online bootstrap preparation, offline build, and offline runtime;
- define the canonical operator bundle layout under `offline_bootstrap/`;
- define cache strategies for Python wheelhouse, npm cache/local registry, Docker image archives/internal registry, and Playwright browser binaries;
- add a no-network strategy check and smoke test;
- wire the strategy check into production readiness gates.

Non-goals:
- do not create or commit actual wheelhouses, npm caches, Docker archives, browser binaries, or local registry data;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior;
- do not resolve npm audit findings in RF1.2.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_check.py --repo-root . --require-ready` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_2_offline_bootstrap_bundle.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.2 runner passes before the verdict commit is considered accepted.

### RF2 — Slides runtime continuation

Goal: turn the accepted slides contracts into a more practical runtime workflow.

Scope candidates:

- baseline `slides_generate` product smoke;
- saved plan to retry flow;
- plan editor to generation linkage;
- task events to artifact history linkage;
- source references to provenance manifest linkage;
- revision/version lineage hardening;
- focused backend/API/frontend E2E tests.

Non-goals:

- do not build a general presentation editor;
- do not add cloud rendering;
- do not introduce internet dependency;
- do not broaden into unrelated document ingestion.

### RF3 — Real document ingestion for DOCX and PDF

Goal: make document workflows useful for real offline files.

Scope candidates:

- real DOCX text extraction;
- safer DOCX editing by instruction;
- text-based PDF extraction;
- honest scanned/image-only PDF failure modes;
- no fake OCR;
- artifact and provenance metadata for extraction results.

Non-goals:

- do not introduce cloud OCR;
- do not claim scanned PDF support before OCR exists;
- do not broaden into a file-format zoo.

### RF4 — Local GigaChat integration hardening

Goal: make the direct local GigaChat production path reliable and diagnosable.

Scope candidates:

- configuration validation for direct local GigaChat;
- endpoint diagnostics and timeouts;
- mocked success/failure tests;
- no silent fallback;
- no silent LiteLLM override;
- clear operator errors when the local endpoint is unavailable.

Non-goals:

- do not make LiteLLM mandatory;
- do not replace GigaChat as default production LLM;
- do not introduce internet runtime;
- do not mix providers silently.

## Baseline after RF0

After RF0 is accepted, run a real deploy/test baseline before RF1 implementation:

- backend `/health`;
- backend `/ready`;
- frontend HTTP response;
- source upload;
- artifact download;
- `slides_generate`;
- `docx_edit`;
- `pdf_summary`;
- full runner;
- Docker runtime smoke with `--skip-build` when images are available.

The baseline results decide the exact RF1/RF2 task order.

## Repository hygiene policy

Canonical planning now lives under `docs/codex/`.

RF0 removes obsolete bootstrap/start-here documents and redundant `.gitkeep`
placeholders when they are no longer needed for tracked non-empty directories.

Readiness-critical files must not be removed until gates are updated in a later,
explicit cleanup task.

Generated files, logs, caches, env files, proxy files, and local dependency
artifacts must not be committed.
