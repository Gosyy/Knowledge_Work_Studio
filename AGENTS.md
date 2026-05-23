# AGENTS.md — KW Studio agent instructions

## Read this first

Before making changes, read these files:

```text
README.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
docs/refactor/CODEX_PROJECT_BRIEFING.md
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
```

For KR-6D work, also read:

```text
docs/refactor/KR6D_reliable_GigaChat_slide_planning_Codex_plan.md
backend/app/services/slides_service/user_prompt_planning.py
backend/app/services/slides_service/service.py
backend/app/services/slides_service/entrypoint.py
backend/app/orchestrator/execution.py
backend/app/api/routes/tasks.py
backend/tests/workflows/test_slides_real_user_prompt_quality.py
backend/tests/workflows/test_slides_source_mode_routing.py
backend/tests/workflows/test_slides_user_prompt_media_baseline.py
backend/tests/smoke/test_public_gigachat_test_mode.py
backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py
backend/tests/smoke/test_rf2_closure_slides_runtime.py
```

## Project identity

KW Studio is an offline/intranet-oriented, artifact-first, provenance-first, operator-gated knowledge-work studio. It is not only a slide generator and not only a chat wrapper.

The product direction is:

```text
source files + user intent
-> workflow plan
-> controlled deterministic tools
-> generated artifacts
-> validation / render / QA
-> provenance / citations / evidence
-> downloadable outputs
-> task history / artifact history / restore / audit
```

Mandatory workflow pillars:

```text
DOCX
PDF
XLSX / Excel
Slides
Python analysis
Browser-assisted evidence
```

## Non-negotiable engineering rules

- Work at senior engineer level.
- Do not make shallow patches or brittle string-anchor edits.
- Do not assume a clean checkout.
- Do not make changes before auditing the relevant files, tests, contracts and runtime state.
- Do not weaken production/offline guardrails to make tests pass.
- Do not patch tests to hide real product failures.
- Do not introduce unsupported claims about offline parity, Kimi-level quality, full Excel feature coverage or full presentation understanding.
- Do not leak secrets in logs, docs, tests or artifacts.
- Do not commit local `.env.deploy`, tokens, Authorization Keys or generated secret values.
- Do not delete legacy files blindly; use audit, policy map, replacement coverage and controlled cleanup.
- Do not use manual `APP_ENV=development` as a public GigaChat testing workaround; use `GIGACHAT_RUNTIME_MODE=public_internet_test`.

## Local-state-aware workflow

Before pulling, patching or running deploy actions, record the actual local state:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/9_Product_Release_Hardening || true
test -f .env.deploy && echo env_present || echo env_absent
docker compose ls || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}' || true
docker volume ls --filter label=com.docker.compose.project=kw-studio || true
```

If the tree is dirty, classify the dirty scope before applying a patch. Do not pull over unknown dirty state.

## Required acceptance process

A successful product patch must close with:

```text
targeted apply/repair runner PASS
commit
full runner PASS
Docker smoke PASS
clean working tree
push
remote verification
```

Use these labels consistently:

```text
TARGETED PASS
LOCAL ACCEPT
REMOTE ACCEPT / CLOSED
FAIL
RUNNER BUG
```

## Required project runners

Use project-resident runners:

```bash
bash scripts/kw_product_full_runner_logged.sh
bash scripts/kw_product_docker_smoke_logged.sh --backend-port 18000 --frontend-port 13000
```

External scripts from a downloads directory are allowed only as apply/bootstrap helpers, not as final validation contracts.

## Logging requirements

Every runner must:

- write logs under the project `logs/` directory;
- duplicate output to terminal;
- archive raw logs as `.log.tar.gz`;
- include report directories when relevant;
- remove raw `.log` after archiving;
- print the archive path.

## Runtime guardrails

### Metadata backend

Production runtime must use Postgres metadata storage. SQLite is allowed only for explicit development/test scope.

### GigaChat runtime modes

```text
GIGACHAT_RUNTIME_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=public_internet_test
```

`public_internet_test` is for temporary operator internet tests only. It is not offline/intranet proof and must warn accordingly.

### Postgres volume credential drift

If `.env.deploy` is regenerated with a new `POSTGRES_PASSWORD`, do not delete only containers while keeping the old Postgres metadata volume. Preserve the password or explicitly reset/migrate the Postgres metadata volume with operator confirmation. Do not delete artifact/storage volumes as a side effect.

## Slides protected contracts

Do not break source-mode routing:

```text
prompt_only + explicit real-user presentation intent -> user prompt planner
prompt_only + short legacy/source-like text -> legacy outline planner
uploaded_source / stored_source -> source-preserving planner
direct internal calls with source_refs or non-default template -> legacy baseline path
```

Do not break RF2/RF2.1 media baseline. Do not leak prompt echo, `Additional insight`, `Local deterministic slide image generation`, `Key points`, `Option A / Current path` or `Step 1` as public PPTX template labels.

## Documentation rules

Update `docs/refactor/PROJECT_MIGRATION_HANDOFF.md` when changing:

- accepted status;
- phase plan;
- workflow contracts;
- runtime modes;
- validation commands;
- operating procedure;
- deploy behavior;
- system dependencies;
- runner behavior;
- profile rules.

Check documentation, CLI help, comments and user-facing text for spelling, stale claims and unsupported claims.

## KR-6D instruction

For reliable GigaChat slide planning, use the detailed plan in:

```text
docs/refactor/KR6D_reliable_GigaChat_slide_planning_Codex_plan.md
```

Do not implement KR-6D as a prompt-only tweak. It requires a versioned schema, typed validation result, robust parser, sanitized diagnostics, one repair retry, honest degraded fallback and real PPTX public-text quality gates.

<!-- KR7_KIMI_LEVEL_SLIDES_AGENT_RULES -->

## KR-7 Kimi-level Slides and test portfolio review

Before implementing KR-7 Slides work, read:

```text
docs/refactor/SLIDES_KIMI_LEVEL_GAP_AUDIT.md
docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md
docs/refactor/ASSISTANT_ENGINEERING_GUIDE_FOR_KIMI_LEVEL_SLIDES.md
docs/refactor/TEST_PORTFOLIO_RATIONALIZATION_PLAN.md
```

KR-7 work must not be implemented as prompt-only tweaks. It must be contract-driven, source-backed, offline-safe, GigaChat-only and quality-gated.

Do not add generated images. Do not create fake charts. Do not introduce local small LLMs. Do not copy external repository code without license/dependency review. Use external projects as references first, and ask the operator for source archives when deeper analysis is needed.

Before deleting or weakening tests, produce a test inventory and classify each test by contract, tier, runtime cost and decision: keep, merge, quarantine, delete or rewrite.

<!-- KR7_LOCAL_FULL_HISTORY_DEV_RULE -->

## Mandatory local full-history development rule

Do not develop, generate code patches, or issue repair runners without an actual local full-history checkout of the project that can be inspected and tested.

Before any code or test patch, verify and record:

```text
git rev-parse --is-shallow-repository  # must be false
git status --short --branch
git log --oneline --decorate --graph -20
git branch -vv
git remote -v
```

If the assistant environment does not have a current local checkout with full Git history, it must stop and ask the operator to provide a separate full-history clone or mirror archive. Work may continue only after that clone/mirror is unpacked, checked out to the current branch, audited, patched and tested locally. GitHub file browsing and uploaded logs are useful evidence, but they are not a substitute for a local full-history project checkout.

<!-- KR7_VENV_ONLY_DEV_RULE -->

## Mandatory `.venv` development rule

All project analysis, code patching and test execution must use the project virtual environment `.venv`.

Before any patch or repair work:

```bash
python3 -m venv .venv          # only if `.venv` is missing
. .venv/bin/activate
python -m pip --version
python -m pytest --version
python -c "import sys; print(sys.executable)"  # must point inside `.venv`
```

If `.venv` exists, activate it and verify required dependencies before running tests. If dependencies are missing, install them into `.venv` through the accepted project dependency path and fix any dependency errors or warnings instead of ignoring them. If `.venv` is missing, create it, install the required project dependencies, then continue only after dependency checks pass.

Do not run targeted tests, full runner helpers, inventory tools or patch validation with system Python when `.venv` is available.


<!-- KR7A1_PYTEST_COLLECTION_AGENT_RULE -->

## Pytest collection and logs

Do not allow pytest to collect test snapshots from `logs/`, `storage/`, frontend build outputs, or recovery report directories. Production/full-suite pytest must be scoped to the real test tree. Runtime logs and evidence bundles are not test sources.
