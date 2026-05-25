# CODEX PROJECT BRIEFING — KW Studio

This document is the project-wide briefing for Codex or any coding agent working on Knowledge_Work_Studio / KW Studio. It is not a task-specific prompt. It defines the operating context, protected contracts and quality rules that every task-specific prompt must follow.

## 1. Project identity

Project name:

```text
Knowledge_Work_Studio / KW Studio
```

Active branch:

```text
9_Product_Release_Hardening
```

Product identity:

```text
KW Studio is an offline/intranet-oriented, artifact-first, provenance-first, operator-gated knowledge-work studio.
```

It is not only a slide generator and not only a chat wrapper around an LLM.

Core direction:

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
DOCX workflow
PDF workflow
XLSX / Excel workflow
Slides workflow
Python analysis workflow
Browser-assisted evidence workflow
```

## 2. Documents to read before editing

Read these before any change:

```text
README.md
AGENTS.md
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
```

For workflow-specific changes, read the relevant files under:

```text
docs/workflows/
docs/quality/
docs/operators/
```

For KR-6D work, additionally read:

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
backend/tests/api/test_k1_valid_pptx_generator.py
backend/tests/api/test_k2_source_aware_presentation_generation.py
backend/tests/api/test_n6_slides_api_schema_stabilization.py
backend/tests/api/test_n7_slides_product_regression.py
backend/tests/smoke/test_public_gigachat_test_mode.py
backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py
backend/tests/smoke/test_rf2_closure_slides_runtime.py
```

## 3. Engineering level

Work as a senior engineer.

Required behavior:

- audit the problem before patching;
- inspect related code, tests, docs, runtime contracts and logs;
- understand upstream and downstream dependencies;
- keep patches explainable, reversible and testable;
- avoid temporary hacks, brittle anchors and hidden assumptions;
- verify syntax, targeted behavior and acceptance coverage;
- update documentation when behavior, contracts or process changes.

Forbidden behavior:

- patching blindly;
- weakening guardrails to make tests pass;
- hiding product failures with test changes;
- relying on unsupported claims;
- assuming a clean checkout;
- ignoring local `.env.deploy`, containers, volumes or running services;
- logging secrets;
- deleting storage/artifact volumes as a side effect.

## 4. Local-state-aware patch planning

Before pulling or patching, record:

```text
branch
local HEAD
remote HEAD
working tree status
untracked files
local-only env files such as .env.deploy
running Docker Compose projects
containers and ports
project Docker volumes
recent relevant logs/evidence
```

If dirty state exists, classify it before making changes. Do not run `git pull` over unknown dirty state. If a previous runner partially applied a patch, continue from that state only after proving the dirty scope is expected.

## 5. Logging and acceptance process

Every apply/repair/bootstrap/full/smoke runner must:

- log under the project `logs/` directory;
- duplicate output to terminal;
- archive logs as `.log.tar.gz`;
- include report directories when relevant;
- remove raw `.log` after archiving;
- print the archive path.

Acceptance labels:

```text
TARGETED PASS        targeted apply/repair checks passed
LOCAL ACCEPT         targeted checks + full runner + Docker smoke passed on committed HEAD
REMOTE ACCEPT/CLOSED commit pushed and remote verified
FAIL                 real project/test/runtime failure
RUNNER BUG           helper/runner bug, not accepted product state
```

A change is not accepted until targeted checks, commit, full runner, Docker smoke, clean tree, push and remote verification are complete.

## 6. Profile neutrality

The project runs across multiple profiles. Product code, Dockerfiles, reusable tests, documentation and readiness gates must remain profile-neutral.

Local paths may appear only in local runner scripts, bootstrap instructions or migration handoff examples.

Known local paths:

```text
Profile 1 and Profile 3 repo: /home/su4ka/workplace/Knowledge_Work_Studio
Profile 1 and Profile 3 downloads: /home/su4ka/Загрузки
Profile 2 repo: /home/editor/workplace/Knowledge_Work_Studio
```

Do not hardcode these paths into product logic.

## 7. Runtime modes and guardrails

### Production/offline-intranet

Default production-oriented runtime:

```text
APP_ENV=production
DEPLOYMENT_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=offline_intranet
METADATA_BACKEND=postgres
LLM_PROVIDER=gigachat
```

Public internet endpoints are not offline/intranet proof.

### Public internet GigaChat test mode

Operator-only test mode:

```text
APP_ENV=production
DEPLOYMENT_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=public_internet_test
LLM_PROVIDER=gigachat
LLM_TRANSPORT_MODE=direct_gigachat
```

This mode may use public GigaChat endpoints for temporary operator tests. It must warn that it is not offline/intranet proof. Do not replace this with manual `APP_ENV=development` overrides.

### Test runtime and development runtime

SQLite remains allowed for explicit development/test metadata scenarios. Fake/noop LLM providers are allowed only as explicit `app_env="test"` doubles. Development runtime must use real GigaChat configuration or an explicit internal LiteLLM transport to GigaChat; it must not silently become a fake/noop provider path. Direct `Settings(...)` tests that expect SQLite/fake behavior must set `app_env="test"` explicitly.

## 8. Postgres volume credential-drift guardrail

If `.env.deploy` is regenerated with a new `POSTGRES_PASSWORD`, the old Postgres metadata volume still contains the old password. Deleting only containers is not enough. Either preserve the old password or explicitly reset/migrate the Postgres metadata volume with operator confirmation.

Do not delete artifact/storage volumes as a side effect.

## 9. Protected contracts

### Workflow contracts

Mature workflows should use or align with:

```text
WorkflowInput
WorkflowPlan
WorkflowRun
WorkflowArtifact
WorkflowManifest
WorkflowQualityReport
WorkflowProvenance
```

### Slides contracts

Protected source-mode routing:

```text
prompt_only + explicit real-user presentation intent -> user prompt planner
prompt_only + short legacy/source-like text -> legacy outline planner
uploaded_source / stored_source -> source-preserving planner
direct internal calls with source_refs or non-default template -> legacy baseline path
```

Protected quality expectations:

- exact requested slide count where the user asks for a count;
- no prompt echo;
- no `Additional insight`;
- no `Local deterministic slide image generation`;
- no public template labels such as `Key points`, `Option A / Current path`, `Step 1`;
- preserve RF2/RF2.1 media baseline;
- preserve render/visual QA bundle contracts.

### LLM runtime topology

- GigaChat is the production/offline provider direction.
- LiteLLM may be an optional gateway transport, not a provider replacement.
- Fake/noop providers are app_env=test doubles only; they are not development runtime providers.
- Runtime endpoint privacy checks must be scoped to the active transport.

## 10. Documentation update rules

Update `PROJECT_MIGRATION_HANDOFF.md` when changing:

```text
accepted status
current or next phase
workflow contracts
runtime modes
validation commands
operating profiles
system dependencies
runner behavior
Docker/deploy behavior
testing methodology
migration instructions
```

Documentation must be checked for spelling, stale claims and unsupported claims.

### Assistant decision-governance documentation maintenance

The assistant decision-governance layer must be maintained when operating rules, prohibitions, Definition of Done, workflow maturity, or documentation stewardship rules change:

```text
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/adr/0001-assistant-decision-governance.md
```

Use `PROJECT_MIGRATION_HANDOFF.md` for durable summaries and links. Do not duplicate long policy blocks across multiple files. Update or add ADRs for cross-cutting decisions. Run `scripts/kw_assistant_governance_check.py --require-ready` before considering the patch ready.

## 11. Negative instructions

Do not:

- use brittle search/replace anchors without verifying current file contents;
- introduce global environment pollution in tests;
- let API test fixtures leak into the full pytest process;
- make checkers read local secret `.env.deploy` when their contract is `.env.deploy.example`;
- claim public internet GigaChat tests prove offline/intranet readiness;
- put fake metadata into artifact manifests;
- put fake hash/size for a manifest self-reference;
- ignore generated files such as `frontend/next-env.d.ts`;
- use `npm audit fix --force` without explicit controlled security task;
- delete legacy docs/scripts without controlled cleanup process.

## 12. Definition of Done for Codex patches

A Codex patch is complete only when:

```text
related files and contracts were audited;
code is changed with minimal, explainable scope;
PROJECT_MIGRATION_HANDOFF.md is updated when required;
new tests cover the intended behavior and failure modes;
py_compile or equivalent syntax checks pass;
targeted tests/checkers pass;
git diff --check passes;
spelling/wording guard passes;
full runner passes on committed HEAD;
Docker smoke passes on committed HEAD;
working tree is clean;
commit is pushed;
remote commit is verified.
```

<!-- LOCAL_FULL_HISTORY_PROJECT_BRIEFING_RULE -->

## Local full-history checkout is mandatory for code work

Do not develop code patches without a local full-history checkout that can be inspected and tested. GitHub browsing, uploaded logs and snippets are not a substitute.

If the coding environment lacks a current full-history checkout, request a full clone or bare mirror archive from the operator, clone from it locally, verify `git rev-parse --is-shallow-repository` is `false`, then reproduce and test the change locally before proposing a patch.

<!-- KR7_VENV_ONLY_DEV_RULE -->

## Use `.venv` for all project checks

Before changing or validating code, activate the project virtual environment:

```bash
cd <project-root>
test -d .venv || python3 -m venv .venv
. .venv/bin/activate
python -c "import sys; print(sys.executable)"
python -m pytest --version
```

If `.venv` is missing dependencies, install the required dependencies into `.venv` and fix any warnings/errors. Do not run tests through system Python when `.venv` exists. A patch validated outside `.venv` is not acceptable project evidence.
