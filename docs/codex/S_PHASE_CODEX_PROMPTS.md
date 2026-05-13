# S Phase Codex Prompts

S-phase begins only after:

```text
R8 verdict: ACCEPT
```

S-phase expands the product deliberately after operator foundation is stable.

## Universal S prompt prefix

```text
Work from repository root on the post-R branch selected by the maintainer.

Before planning, verify:
- R8 verdict: ACCEPT exists in branch history.
- working tree is clean.
- current branch is the intended S branch.

Implement this S issue only.

Use a repo-root Python apply script:
apply_sX_<slug>.py

Inspect live file contents before patching.
Keep changes narrow, testable, and documented.
Do not introduce internet runtime dependencies.
Do not print or commit secrets.
Preserve modular monolith architecture.
```

## S1 — Offline three-server LLM topology and local GigaChat hardening

```text
Implement S1 only.

Goal:
Document and harden the default offline LLM path:
KW Studio Server 1 → local GigaChat Server 3 by internal ip:port.

Allowed scope:
- docs/offline-three-server-topology.md
- docs/local-gigachat-provider.md
- docs/llm-provider-contract.md
- .env.deploy.example
- backend/app/core/config.py
- backend/app/integrations/llm/providers.py
- backend/app/integrations/llm/factory.py
- backend/tests/integrations/test_local_gigachat_provider.py

Requirements:
1. GigaChat remains default production LLM.
2. Add explicit local endpoint docs.
3. Support internal ip:port config.
4. Add auth mode planning/implementation only if scoped:
   oauth | bearer | none.
5. Do not require LiteLLM for default production mode.
6. Do not require internet.
7. Redact all secrets.

Forbidden:
- no cloud provider default;
- no external endpoint default;
- no model runtime on Server 1;
- no LiteLLM SDK dependency in Server 1;
- no hardcoded real IPs/secrets.

Acceptance:
python3 -m pytest backend/tests/integrations/test_local_gigachat_provider.py -q
python3 scripts/kw_env_validate.py --env-file .env.deploy.example --allow-placeholders
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## S2 — Workflow contracts

```text
Implement S2 only.

Goal:
Create explicit workflow contracts for product capabilities.

Allowed files:
- docs/contracts/docx-workflow.md
- docs/contracts/pdf-workflow.md
- docs/contracts/slides-workflow.md
- docs/contracts/data-analysis-workflow.md
- docs/contracts/browser-assisted-workflow.md
- docs/contracts/llm-provider-contract.md
- docs/contracts/README.md

Each contract must define:
- inputs;
- outputs;
- artifact types;
- source refs/provenance;
- side effects;
- failure modes;
- retry behavior;
- security constraints;
- acceptance tests.

Forbidden:
- no service rewrites;
- no prompt-only behavior changes;
- no new runtime dependencies.

Acceptance:
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## S3 — Slides outline-first UX

```text
Implement S3 only.

Goal:
Make slides generation outline-first with editable plan approval.

Pipeline:
sources / prompt → extraction → outline → editable slide plan → approval → PPTX generation

Requirements:
1. user can inspect plan before PPTX generation;
2. plan is versioned/snapshotted;
3. generation can retry from saved plan;
4. source refs are preserved where available.

Forbidden:
- no template marketplace;
- no external theme service;
- no broad UI redesign;
- no removal of current revision/version behavior.
```

## S4 — Adaptive/template deck modes

```text
Implement S4 only.

Goal:
Add two slide generation modes inspired by Kimi Slides:
- Adaptive / plan-driven mode
- Template-driven mode

Requirements:
1. mode is explicit in plan metadata;
2. template mode uses local templates only;
3. adaptive mode does not require internet;
4. mode selection happens after outline/plan creation;
5. existing PPTX export remains deterministic.

Forbidden:
- no external template store;
- no cloud asset lookup;
- no dependency on online images.
```

## S5 — Task event stream and failure recovery

```text
Implement S5 only.

Goal:
Make long-running workflows observable and recoverable.

Event examples:
- task.created
- sources.loaded
- plan.generated
- plan.awaiting_approval
- runtime.started
- artifact.created
- task.failed
- task.retry_available
- task.completed

Requirements:
1. tasks expose structured events;
2. UI can show timeline;
3. failure reason is visible and safe;
4. retry from saved plan is possible where supported;
5. secrets and internal storage keys are never exposed.

Forbidden:
- no distributed event bus;
- no Kafka/RabbitMQ requirement;
- no realtime collaboration system.
```

## S6 — Source-to-artifact provenance

```text
Implement S6 only.

Goal:
Track sources through task execution to generated artifacts and versions.

Requirements:
1. artifact has source refs;
2. presentation slide/plan can carry source refs;
3. download/history UI shows safe provenance summaries;
4. no internal storage IDs leak.
```

## S7 — Browser-assisted internal workflows

```text
Implement S7 only.

Goal:
Enable browser-assisted internal workflows for offline/intranet tasks.

Allowed uses:
- intranet web page capture;
- browser rendering;
- PDF/browser visual verification;
- slide screenshot QA;
- source citation capture.

Rules:
1. browser runtime remains internal-only unless explicitly changed later;
2. no autonomous user-facing browser agent;
3. no login/form-submit/purchase/destructive action without approval;
4. no internet assumption.
```

## S8 — Optional LiteLLM-compatible gateway and heavy-node integrations

```text
Implement S8 only.

Goal:
Add optional LiteLLM-compatible provider for Server 2 gateway.

Topology:
Server 1 KW Studio → Server 2 LiteLLM-compatible gateway → Server 3 local GigaChat.

Requirements:
1. GigaChat remains default production LLM.
2. LiteLLM is optional gateway, not required default.
3. Ollama/local models are fallback/dev only.
4. Server 1 uses thin HTTP client; no LiteLLM SDK dependency in app image.
5. Secrets are redacted.
6. All endpoints are internal ip:port in offline mode.

Forbidden:
- no replacing GigaChat default;
- no internet endpoints as default;
- no model runtime on Server 1;
- no broad LLM service rewrite.
```

## S9 — Multimodal/visual QA planning layer

```text
Implement S9 planning only unless explicitly approved for code.

Goal:
Plan visual QA for slides/PDF artifacts using local/offline capabilities.

Possible future functions:
- slide screenshot QA;
- PDF layout/table inspection;
- chart verification;
- image-supported document understanding.

Forbidden in planning phase:
- no new model dependency;
- no internet service;
- no OCR stack unless explicitly scoped.
```
