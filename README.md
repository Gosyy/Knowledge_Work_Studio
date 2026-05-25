# KW Studio — Knowledge Work Studio

KW Studio is an offline/intranet-oriented, artifact-first, provenance-first, operator-gated knowledge-work studio. It turns user intent, uploaded source files, structured data, browser evidence, Python analysis and controlled local or intranet LLM assistance into downloadable, validated and auditable work artifacts.

KW Studio is not only a slide generator and not only a chat wrapper. The product direction is a workflow studio where every serious action should produce a traceable artifact bundle rather than an unverified chat answer.

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

## What the project is for

The project is intended for internal knowledge-work automation in environments where operators need verifiable outputs and controlled runtime behavior. It is designed for use cases such as:

- creating or transforming DOCX work products;
- summarizing or reporting on PDF content;
- inspecting XLSX / CSV data and generating workbook evidence;
- generating PPTX presentations with render and visual QA artifacts;
- running controlled Python analysis;
- collecting browser-assisted evidence through explicit, operator-gated workflows;
- preserving provenance, manifests, quality reports and downloadable artifacts for audit.

The core principle is: **the system should explain what it did, what sources it used, what artifacts it created, and what validations passed or failed.**

## Product pillars

The first-class workflow pillars are:

| Pillar | Purpose | Expected artifact behavior |
| --- | --- | --- |
| DOCX | Produce or transform Word-like work products. | Output documents, manifests, quality reports and provenance. |
| PDF | Summarize, report on, or inspect PDF content. | Source-grounded reports, extracted evidence, quality metadata. |
| XLSX / Excel | Inspect spreadsheets and tabular data. | Workbook metadata, formula inventory, previews, manifests. |
| Slides | Generate or continue PPTX presentations. | PPTX, slide plan, render manifests, visual QA, provenance. |
| Python analysis | Run controlled deterministic analysis. | Scripts/results/charts/logs with reproducible metadata. |
| Browser evidence | Use browser-assisted evidence when explicitly enabled. | Evidence manifests, captured references and audit trail. |

## Current development status

KW Studio is in active product hardening. The repository contains production-oriented validation runners, Docker smoke checks, workflow contracts and first concrete workflow bundles. The application can be started locally for operator testing, and it includes explicit runtime modes for offline/intranet assumptions and public internet GigaChat testing.

The project is not yet a finished end-user SaaS product. The current web interface is a workspace shell with artifact/history surfaces. Some workflows are mature enough for regression and smoke validation, while others are still being hardened for real user quality.

Current important status notes:

- Backend task/session/artifact APIs are available through FastAPI.
- Docker deploy uses Postgres metadata storage and local artifact storage by default.
- Public internet GigaChat testing must use `GIGACHAT_RUNTIME_MODE=public_internet_test` and must not be treated as offline/intranet proof.
- Slides generation has source-mode routing and public-internet test support, but reliable LLM slide planning is the next hardening target.
- The repository contains strict acceptance runners; passing a small targeted check is not enough for local or remote acceptance.

## Repository layout

The exact tree may evolve, but the main project surfaces are:

```text
backend/                 FastAPI backend, services, workflow logic, tests
frontend/                Next.js workspace shell and browser UI
scripts/                 Project-resident runners, gates, operator tools
skills/                  Deterministic artifact/document skills used by workflows
infra/                   System package lists and deployment support
outputs/                 Local output area when used by workflows/tests
docs/                    Product, architecture, workflow, quality and refactor docs
docs/refactor/           Migration handoff, KR roadmap, Codex briefing and phase plans
docker-compose.deploy.yml  Postgres-backed local deploy profile
.env.deploy.example      Checked-in deployment example without real secrets
```

## High-level architecture

KW Studio is a modular monolith. It keeps product workflow services inside one backend process while preserving clear module boundaries.

```text
Browser UI / operator tools
        |
        v
FastAPI routes
        |
        v
Session / task / artifact APIs
        |
        v
Orchestrator and workflow services
        |
        +--> DOCX / PDF / XLSX / Slides / Python / Browser workflows
        |
        +--> deterministic skills and render tools
        |
        +--> LLM provider adapter when allowed by runtime mode
        |
        v
Artifact storage + metadata repository
        |
        v
Manifests, provenance, quality reports and downloadable outputs
```

## Module descriptions and module schemes

### Frontend workspace shell

The frontend is a Next.js workspace shell. It is responsible for presenting the operator-facing work area: task surfaces, artifact history, presentation surfaces and future chat-like workflow interactions. It should not contain business workflow logic.

Scheme:

```text
Operator browser
  -> Next.js pages/components
  -> API client calls
  -> backend sessions/tasks/artifacts
  -> downloadable artifacts and task history
```

Responsibilities:

- render workspace pages;
- call backend APIs;
- display task/artifact state;
- keep UI logic separate from backend workflow rules.

Limitations:

- the current UI is not the final full chat experience;
- backend APIs are often more complete than the visible shell;
- user-facing presentation generation quality is still being hardened.

### FastAPI route layer

The backend route layer exposes health, readiness, session, task, artifact and workflow endpoints. Routes should remain thin: validate input, call services, return structured responses.

Scheme:

```text
HTTP request
  -> FastAPI route
  -> Pydantic request/response contract
  -> service or orchestrator
  -> response with task/artifact metadata
```

Responsibilities:

- expose stable API contracts;
- avoid hidden runtime decisions in route handlers;
- keep errors honest and inspectable;
- use dependency injection rather than global side effects.

### Session, task and artifact services

These services model user work as sessions, tasks and downloadable artifacts. A session groups related work. A task records the requested operation and its lifecycle. An artifact stores a generated or derived output with metadata.

Scheme:

```text
Session
  -> Task
      -> execution input
      -> workflow run
      -> artifact ids
          -> artifact metadata
          -> downloadable file
```

Responsibilities:

- create and retrieve sessions;
- create, execute and inspect tasks;
- persist result data and error state;
- register artifacts and downloads;
- preserve ownership and provenance metadata.

### Orchestrator and execution coordinator

The orchestrator connects task intent, source inputs and workflow services. It should decide which service handles a task without hiding validation or provenance behavior.

Scheme:

```text
Task + sources + user content
  -> execution coordinator
  -> workflow request object
  -> workflow service
  -> workflow result
  -> task result and artifacts
```

Responsibilities:

- build execution input from uploaded/stored/document/presentation sources;
- preserve source mode information;
- route to the correct workflow service;
- keep source-aware behavior compatible with existing contracts.

### Workflow contract core

Workflow contracts define shared vocabulary for mature workflows: input, plan, run, artifact, manifest, quality report and provenance. They are the architectural bridge between user intent and auditable output.

Scheme:

```text
WorkflowInput
  -> WorkflowPlan
  -> WorkflowRun
  -> WorkflowArtifact
  -> WorkflowManifest
  -> WorkflowQualityReport
  -> WorkflowProvenance
```

Responsibilities:

- make workflow outputs comparable and inspectable;
- encourage artifact bundles rather than one-off files;
- support validation and provenance-first design;
- keep future DOCX/PDF/XLSX/Slides/Python/Browser workflows aligned.

### Metadata repository layer

The metadata repository abstracts persistence for sessions, tasks, artifacts and related records. Production-like Docker deploy uses Postgres. SQLite is allowed only for development/test scenarios when explicitly permitted.

Scheme:

```text
Service call
  -> repository interface
  -> Postgres runtime backend OR explicit SQLite test backend
  -> persisted metadata
```

Responsibilities:

- keep runtime metadata durable;
- reject unsafe production SQLite configurations;
- support deterministic test isolation;
- avoid silently switching metadata truth layers.

### Artifact storage layer

The storage layer stores files created by workflows. In local/intranet Docker deploy, local storage can be used when it points to an approved disk, NAS or mounted internal volume.

Scheme:

```text
Workflow output file
  -> artifact storage path
  -> artifact metadata record
  -> download endpoint
```

Responsibilities:

- store generated artifacts;
- preserve size/hash/addressing metadata where required;
- support artifact history and download;
- avoid deleting storage volumes as a side effect of metadata resets.

### DOCX workflow

The DOCX pillar is intended to create or transform Word-like documents while preserving artifact traceability.

Scheme:

```text
DOCX/source content + user intent
  -> document workflow plan
  -> deterministic document operations
  -> generated DOCX/report artifacts
  -> manifest + quality report + provenance
```

Responsibilities:

- produce downloadable document artifacts;
- preserve source references where available;
- fail honestly when document assumptions cannot be validated.

### PDF workflow

The PDF pillar supports source-grounded summarization, reporting or inspection of PDF content.

Scheme:

```text
PDF source
  -> extraction/inspection
  -> source evidence
  -> report/summary artifact
  -> quality and provenance bundle
```

Responsibilities:

- avoid unsupported claims;
- preserve evidence references;
- produce auditable reports rather than ungrounded chat text.

### XLSX / CSV workflow

The XLSX pillar inspects spreadsheet structure and data. It is mandatory product coverage, not an optional add-on.

Scheme:

```text
Workbook / CSV
  -> sheet metadata
  -> formula inventory
  -> table previews
  -> evidence manifest
  -> artifact manifest + quality report
```

Responsibilities:

- expose workbook structure;
- track formulas and previews;
- produce machine-readable manifests;
- avoid claiming complete Excel feature coverage unless proven.

### Slides workflow

The Slides pillar creates or continues PPTX decks. It includes source-aware routing, media baseline behavior, render/visual QA artifacts and public text quality concerns.

Scheme:

```text
Prompt and/or sources
  -> source-mode routing
  -> slide plan
  -> PPTX generation
  -> render to PDF/PNG when QA requires it
  -> geometry/visual QA reports
  -> artifact manifest and provenance
```

Protected routing contracts:

```text
prompt_only + explicit real-user presentation intent -> user prompt planner
prompt_only + short legacy/source-like text -> legacy outline planner
uploaded_source / stored_source -> source-preserving planner
direct internal calls with source_refs or non-default template -> legacy baseline path
```

Current known quality target:

- reliable GigaChat slide planning must move from opportunistic fallback to a typed, validated, repairable JSON planning contract;
- generated public PPTX text must not leak prompt echoes, placeholder labels or internal technical labels.

### LLM integration layer

The LLM integration layer selects and validates the runtime provider. Production/offline mode is GigaChat-first. LiteLLM may be an optional gateway transport. Fake/noop providers are explicit test doubles only, not development, production, or offline runtime providers. Ollama/local-small-LLM endpoints are not part of active product runtime scope.

Scheme:

```text
Settings
  -> runtime mode validation
  -> transport selection
  -> provider adapter
  -> workflow service call
```

Runtime modes:

```text
GIGACHAT_RUNTIME_MODE=offline_intranet       default offline/intranet mode
GIGACHAT_RUNTIME_MODE=public_internet_test   explicit operator public internet test mode
```

`public_internet_test` is only for temporary operator internet tests with public GigaChat endpoints. It is not offline/intranet deployment proof.

### Python analysis workflow

Python analysis is a controlled deterministic tool surface for data and artifact generation.

Scheme:

```text
input files/data
  -> controlled Python runtime
  -> analysis result files/charts/tables
  -> artifacts + logs + quality metadata
```

Responsibilities:

- preserve reproducibility;
- log execution evidence;
- avoid uncontrolled arbitrary automation beyond the intended runtime boundary.

### Browser-assisted evidence workflow

Browser assistance is intended as an evidence-gathering pillar, not a general autonomous browser-agent product.

Scheme:

```text
operator-approved browser task
  -> evidence collection
  -> references/captures/metadata
  -> evidence manifest
  -> workflow artifact bundle
```

Responsibilities:

- remain operator-gated;
- preserve citations/evidence;
- avoid unsupported browsing claims.

### Render and visual QA stack

Render QA is required for presentation quality checks. LibreOffice and poppler are functional dependencies, not merely optional binaries.

Scheme:

```text
PPTX
  -> LibreOffice PDF export
  -> poppler/pdftoppm PNG render
  -> geometry and visual QA reports
  -> artifact manifest coverage
```

Responsibilities:

- prove that decks can render;
- detect empty or broken output surfaces;
- include render artifacts in quality bundles when required.

### Deployment and operator runners

Project-resident runners are the source of truth for validation. External scripts in a downloads directory are allowed only as bootstrap/apply helpers.

Scheme:

```text
apply/repair runner
  -> targeted checks
  -> commit
  -> full runner
  -> Docker smoke
  -> push
  -> remote verification
```

Important runners:

```text
scripts/kw_product_full_runner_logged.sh
scripts/kw_product_docker_smoke_logged.sh
scripts/kw_full_tests_with_proxy_runner.sh
scripts/deploy/kw_postgres_volume_guardrail.py
```

## Runtime modes

### Development/test mode

Used for local development and automated tests. SQLite remains local/test-scoped; fake/noop LLM providers are allowed only as explicit automated-test doubles.

Typical properties:

```text
APP_ENV=test or development
METADATA_BACKEND=sqlite when explicitly allowed
LLM_PROVIDER=fake for automated-test-only behavior
```

### Offline/intranet mode

Default production-oriented mode. Public internet endpoints are not offline/intranet proof.

Typical properties:

```text
APP_ENV=production
DEPLOYMENT_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=offline_intranet
METADATA_BACKEND=postgres
LLM_PROVIDER=gigachat
LLM_TRANSPORT_MODE=direct_gigachat or litellm_gateway
```

### Public internet GigaChat test mode

Explicit operator mode for testing with public GigaChat endpoints and an Authorization Key-derived credential pair.

Typical properties:

```text
APP_ENV=production
DEPLOYMENT_MODE=offline_intranet
GIGACHAT_RUNTIME_MODE=public_internet_test
LLM_PROVIDER=gigachat
LLM_TRANSPORT_MODE=direct_gigachat
```

This mode must emit warnings and must not be used as evidence that offline/intranet deployment is ready.

## Local setup

### Python and Node dependencies

```bash
cd /home/su4ka/workplace/Knowledge_Work_Studio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd frontend
npm ci
cd ..
```

### System dependencies

The render stack requires system packages such as LibreOffice, poppler utilities and fonts. See:

```text
infra/system-packages/ubuntu-render-stack.txt
```

Docker and Docker Compose v2 are required for deploy and smoke validation.

## Local run and deploy

### Backend development run

Use project Makefile or backend commands according to the current environment. Always check the current project scripts before assuming a command.

Basic health checks:

```bash
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/ready
```

### Docker deploy run

A local deploy uses:

```text
docker-compose.deploy.yml
.env.deploy
```

Do not commit `.env.deploy`; it contains local secrets.

Basic command:

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio up -d --build
```

### Postgres volume credential-drift guardrail

If `.env.deploy` is regenerated with a new `POSTGRES_PASSWORD`, do not remove only containers while keeping the old Postgres metadata volume. Either preserve the old password or explicitly reset/migrate the Postgres metadata volume with operator confirmation.

The project contains a helper:

```bash
python scripts/deploy/kw_postgres_volume_guardrail.py --help
```

Storage/artifact volumes must not be deleted as a side effect of resetting metadata.

## Validation and acceptance

Patch acceptance labels:

```text
TARGETED PASS        apply/repair runner and targeted checks passed
LOCAL ACCEPT         targeted checks + full runner + Docker smoke passed on committed HEAD
REMOTE ACCEPT/CLOSED commit pushed and remote verified
FAIL                 product/test/syntax/validation/runtime failure
RUNNER BUG           helper or runner behavior failed independently of product logic
```

Full validation:

```bash
cd /home/su4ka/workplace/Knowledge_Work_Studio
bash scripts/kw_product_full_runner_logged.sh
bash scripts/kw_product_docker_smoke_logged.sh --backend-port 18000 --frontend-port 13000
```

A patch is not accepted until logs are reviewed. Do not call a patch accepted based only on targeted tests.

## Debugging guide

### Health/readiness

```bash
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/ready
```

### Docker state

```bash
docker compose --env-file .env.deploy -f docker-compose.deploy.yml -p kw-studio ps
docker logs --tail=200 kw-studio-backend-1
docker logs --tail=120 kw-studio-postgres-1
docker logs --tail=120 kw-studio-frontend-1
```

### Common runtime issues

| Symptom | Likely cause | Correct action |
| --- | --- | --- |
| Backend unhealthy after env regeneration | New `POSTGRES_PASSWORD` with old Postgres volume | Preserve password or reset/migrate metadata volume explicitly. |
| Public GigaChat endpoints rejected | Running in `GIGACHAT_RUNTIME_MODE=offline_intranet` | Use explicit `public_internet_test` for operator internet tests only. |
| SQLite rejected | `APP_ENV=production` with `METADATA_BACKEND=sqlite` | Use Postgres for production or explicit test/dev settings. |
| Next.js modifies `frontend/next-env.d.ts` | Generated build file | Restore unless intentionally changed. |
| Docker permission denied | User session not refreshed after docker group change | Refresh login/session before treating as project failure. |

## Limitations

- KW Studio is in active product hardening.
- The current UI is a workspace shell and not the final full chat UX.
- Public internet GigaChat test mode is not offline/intranet proof.
- Reliable real LLM slide planning is still being hardened under KR-6D.
- Do not claim complete Excel feature coverage, full presentation understanding, Kimi-level quality or full offline parity without accepted evidence.
- Browser assistance is an evidence workflow pillar, not a broad autonomous browser-agent product.

## Documentation entry points

Start with:

```text
README.md
AGENTS.md
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
docs/refactor/CODEX_PROJECT_BRIEFING.md
docs/refactor/KR6D_reliable_GigaChat_slide_planning_Codex_plan.md
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
docs/workflows/
docs/quality/
docs/operators/
```

`PROJECT_MIGRATION_HANDOFF.md` is the durable continuation source for process rules, profiles, guardrails and accepted operating procedure.

<!-- KR7_KIMI_LEVEL_SLIDES_ROADMAP_LINKS -->

## Slides Kimi-level roadmap and test portfolio review

The Slides pillar is moving from validated LLM planning toward professional, source-backed, editable presentation generation. KR-6D proves that GigaChat can return a validated slide plan, but it does not claim professional Kimi-level deck quality.

Current planning documents:

```text
docs/refactor/SLIDES_KIMI_LEVEL_GAP_AUDIT.md
docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md
docs/refactor/ASSISTANT_ENGINEERING_GUIDE_FOR_KIMI_LEVEL_SLIDES.md
docs/refactor/TEST_PORTFOLIO_RATIONALIZATION_PLAN.md
```

Important constraints:

- production/offline mode has no public internet;
- GigaChat is the only LLM runtime;
- local small LLMs, Ollama endpoints, and arbitrary model selectors are not part of the target runtime;
- images must be selected from uploaded documents/templates/assets, not generated;
- charts must be backed by real data;
- professional quality claims require content/design/coherence/data/assets/export gates.
