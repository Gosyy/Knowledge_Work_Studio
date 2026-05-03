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

### RF1.3 — Offline bootstrap manifest and bundle validation tooling

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.3 full runner, and a separate `RF1.3 verdict: ACCEPT` commit.

Scope:
- define the portable `offline_bootstrap/manifest.json` schema;
- add a no-network manifest schema check that passes without requiring an actual bundle;
- add optional validation for an operator-provided bundle directory;
- cover the optional bundle path with a temporary smoke-test fixture;
- wire the manifest check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not populate npm caches;
- do not save Docker image archives;
- do not install Playwright browsers;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_manifest_check.py --repo-root . --require-ready` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_3_offline_bootstrap_manifest.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.3 runner passes before the verdict commit is considered accepted.

### RF1.4 — Offline bundle verification CLI and template generation

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.4 full runner, and a separate `RF1.4 verdict: ACCEPT` commit.

Scope:
- add a no-network CLI for offline bundle policy checks;
- add template generation for an operator-provided `offline_bootstrap/` directory;
- add bundle layout and manifest verification;
- add smoke tests using temporary bundle directories;
- update git hygiene so root-level `offline_bootstrap/` is ignored;
- wire the RF1.4 policy check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not run npm install/cache commands;
- do not pull or save Docker images;
- do not install Playwright browsers;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-policy --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_4_offline_bootstrap_bundle_tooling.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.4 runner passes before the verdict commit is considered accepted.

### RF1.5 — Offline bundle artifact presence checks and operator runbook commands

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.5 full runner, and a separate `RF1.5 verdict: ACCEPT` commit.

Scope:
- add explicit artifact presence validation for an operator-provided `offline_bootstrap/` bundle;
- add operator runbook commands for Python wheelhouse, npm cache, Docker images, Playwright browsers, and checksums;
- add `check-artifact-policy`, `verify-artifacts`, and `print-runbook` CLI surfaces;
- cover artifact presence validation with temporary smoke-test fixtures;
- wire only the no-network RF1.5 policy check into production readiness gates.

Non-goals:
- do not run `pip download`;
- do not run `pip install`;
- do not run `npm ci`;
- do not run `npm cache`;
- do not run `docker pull`;
- do not run `docker save`;
- do not install Playwright browsers;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-artifact-policy --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_5_offline_bundle_artifact_presence.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.5 runner passes before the verdict commit is considered accepted.

### RF1.6 — Offline checksum and artifact integrity verification

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.6 full runner, and a separate `RF1.6 verdict: ACCEPT` commit.

Scope:
- add checksum integrity policy for operator-provided `offline_bootstrap/` bundles;
- add `check-integrity-policy` and `verify-checksums` CLI surfaces;
- parse and validate SHA-256 entries from `checks/sha256sums.txt`;
- reject malformed hashes, missing files, absolute paths, and parent traversal;
- cover valid and corrupted checksum scenarios with temporary smoke-test fixtures;
- wire only the no-network RF1.6 policy check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not run npm install/cache commands;
- do not pull or save Docker images;
- do not install Playwright browsers;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-integrity-policy --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_6_offline_bundle_integrity.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.6 runner passes before the verdict commit is considered accepted.

### RF1.7 — Offline artifact inventory summaries and expected image/package listing

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.7 full runner, and a separate `RF1.7 verdict: ACCEPT` commit.

Scope:
- add expected offline profile derivation from Python, npm, Docker, Compose, and Playwright source files;
- add `check-inventory-policy`, `expected-profile`, and `inventory-summary` CLI surfaces;
- summarize operator bundle artifacts without downloading or installing anything;
- compare Docker `images-manifest.txt` entries against expected images;
- cover template, populated, and missing-expected-image inventory scenarios with temporary smoke-test fixtures;
- wire only the no-network RF1.7 policy check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not run npm install/cache commands;
- do not pull or save Docker images;
- do not install Playwright browsers;
- do not resolve npm audit findings;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-inventory-policy --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_7_offline_artifact_inventory.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.7 runner passes before the verdict commit is considered accepted.

### RF1.8 — Offline build recipe dry-run and bundle readiness report

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.8 full runner, and a separate `RF1.8 verdict: ACCEPT` commit.

Scope:
- add a no-network readiness policy check for the RF1 offline bundle report layer;
- add `bundle-readiness-report` to aggregate layout, artifact presence, checksum, inventory, and expected profile status;
- add `offline-build-dry-run` to print operator build/runtime recipe steps without executing them;
- cover ready and not-ready bundles with temporary smoke-test fixtures;
- wire only the no-network RF1.8 policy check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not run npm install/cache commands;
- do not pull or save Docker images;
- do not install Playwright browsers;
- do not run offline build commands automatically;
- do not resolve npm audit findings;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-readiness-policy --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_8_offline_build_readiness.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.8 runner passes before the verdict commit is considered accepted.

### RF1.9 — Offline operator command groups and RF1 closure checkpoint

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.9 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF1.9 verdict: ACCEPT` commit.

Scope:
- add a no-network RF1 closure policy check;
- add `operator-command-groups` to group RF1 operator commands by operational intent;
- add `rf1-closure-report` to summarize RF1.1–RF1.9 closure status and next phase options;
- document the transition decision: RF2 slides runtime or a separate controlled dependency/security step;
- wire only the no-network RF1.9 closure policy check into production readiness gates.

Non-goals:
- do not download Python wheels;
- do not run npm install/cache commands;
- do not pull or save Docker images;
- do not install Playwright browsers;
- do not run offline build commands automatically;
- do not run `npm audit fix --force`;
- do not change dependency versions;
- do not change Docker build logic;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py check-closure-policy --repo-root . --require-ready --json` passes;
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py operator-command-groups --repo-root . --json` passes;
- `python3 scripts/kw_offline_bootstrap_bundle_tool.py rf1-closure-report --repo-root . --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_9_offline_operator_command_groups.py -q` passes;
- `python3 scripts/kw_production_readiness_gate.py --repo-root . --skip-backend --skip-frontend --skip-e2e` passes;
- the full post-RF1.9 runner and Docker runtime smoke pass before the verdict commit is considered fully accepted.

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



### RF1.10 — Controlled dependency/security baseline assessment without forced upgrades

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF1.10 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF1.10 verdict: ACCEPT` commit.

Scope:
- add a no-network dependency/security assessment policy;
- report current frontend, Python, and Docker dependency surfaces;
- allow optional read-only npm audit JSON summarization;
- preserve the rule that `npm audit fix --force` is forbidden without a separate controlled patch;
- keep dependency/security analysis separate from RF2 slides runtime work.

Non-goals:
- do not run `npm audit fix`;
- do not run `npm audit fix --force`;
- do not change `frontend/package.json`;
- do not change `frontend/package-lock.json`;
- do not change `requirements.txt`;
- do not change Dockerfiles;
- do not change runtime behavior.

Acceptance:
- `python3 scripts/kw_controlled_dependency_security_assessment.py --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf1_10_controlled_dependency_security_assessment.py -q` passes;
- production readiness includes the RF1.10 assessment policy check;
- full post-RF1.10 runner and Docker runtime smoke pass before final acceptance.


### RF2.1 — Slides runtime capability inventory and baseline smoke

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.1 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.1 verdict: ACCEPT` commit.

Scope:
- inventory current slides service/API/frontend/test runtime surfaces;
- run a no-network baseline PPTX smoke through existing `SlidesService.generate_deck`;
- classify capabilities as baseline-runtime-ready, partial runtime, product gap, or contract-only;
- explicitly record that the current deterministic generator is not proven Kimi-grade;
- explicitly record that the whole slides product loop is not proven Kimi-level;
- prepare the RF2.2 handoff for deterministic PPTX generation from an approved plan.

Non-goals:
- do not claim Kimi-level slides quality from generator existence alone;
- do not treat generator maturity as whole-project maturity;
- do not change renderer behavior;
- do not change service/API behavior;
- do not change persistence behavior;
- do not change frontend behavior;
- do not change dependency versions;
- do not change Dockerfiles;
- do not change LLM topology;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_runtime_inventory_check.py --repo-root . --require-ready --json` passes;
- checker reports `kimi_grade_supported: false`;
- checker reports `current_generator_grade: baseline_deterministic_not_kimi_grade`;
- checker reports `whole_project_kimi_level_supported: false`;
- checker reports `product_loop_grade: baseline_inventory_not_kimi_level_project`;
- `python3 -m pytest backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py -q` passes;
- selected existing slides service PPTX smoke passes;
- S3-S7 slides contract checks pass;
- RF2.0 checkpoint check passes;
- production readiness includes the RF2.1 inventory checkpoint;
- full post-RF2.1 runner and Docker runtime smoke pass before final acceptance.

### RF2.0 — Slides runtime phase kickoff and scope checkpoint

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.0 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.0 verdict: ACCEPT` commit.

Scope:
- create the RF2 slides runtime phase plan;
- add a no-network RF2.0 checkpoint validator;
- preserve RF1 offline/intranet foundation constraints;
- preserve accepted S3-S7 slides contract surfaces;
- prepare the next step, RF2.1, as runtime capability inventory and baseline smoke.

Non-goals:
- do not change renderer behavior;
- do not change slides task runtime behavior;
- do not change dependency versions;
- do not change Dockerfiles;
- do not change LLM topology;
- do not run `npm audit fix --force`;
- do not start RF2.1 until RF2.0 is accepted.

Acceptance:
- `python3 scripts/kw_slides_runtime_phase_check.py --repo-root . --require-ready --json` passes;
- `python3 -m pytest backend/tests/smoke/test_rf2_0_slides_runtime_phase.py -q` passes;
- existing S3-S7 slides contract checks pass;
- production readiness includes the RF2.0 checkpoint;
- full post-RF2.0 runner and Docker runtime smoke pass before final acceptance.

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

### RF2.2 — Minimal deterministic PPTX generation from approved plan

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.2 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.2 verdict: ACCEPT` commit.

Scope:
- add an additive backend runtime path for approved `PresentationPlan` rendering;
- introduce `ApprovedPlanRenderRequest` and `ApprovedPlanRenderResult`;
- add `render_approved_plan_to_pptx`;
- add `SlidesService.generate_deck_from_approved_plan`;
- return deterministic PPTX bytes, sha256, size, slide count, render mode, template id, safe metadata, and safe event hints.

Non-goals:
- do not add a public API endpoint yet;
- do not persist generated artifacts yet;
- do not emit downloadable provenance manifest yet;
- do not implement saved-plan retry yet;
- do not implement visual QA runtime;
- do not claim Kimi-level slides quality;
- do not change dependency versions;
- do not change Dockerfiles;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_approved_plan_runtime_check.py --repo-root . --require-ready --json` passes;
- smoke tests prove deterministic approved-plan PPTX rendering;
- unapproved plans are rejected;
- template mode requires explicit local template id;
- production readiness includes RF2.2;
- full post-RF2.2 runner and Docker runtime smoke pass before final acceptance.
