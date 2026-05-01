# KW Studio R and S Master Plan

## Product identity

KW Studio is an artifact-first offline/intranet knowledge-work studio.

It turns user files and natural-language tasks into finished, downloadable,
versioned, and auditable work products:
- edited DOCX
- summarized PDF
- generated PPTX
- spreadsheet/CSV data analysis
- charts and tabular artifacts
- task plans, outlines, source references, and version history

## Non-negotiable architecture identity

KW Studio v1 is a modular monolith.

Do not turn it into:
- a microservice platform;
- a cloud deployment framework;
- a general autonomous browser agent product;
- a general app builder;
- a broad file-format zoo.

## Current status

Accepted R-phase verdicts:
- R1 — full-stack Docker Compose smoke gate
- R2 — Postgres schema lifecycle and migration preflight
- R3 — Artifact download UI and export history panel
- R4 — Restore audit metadata and safer confirmation UX
- R5 — Operator deployment runbook, backup, and restore drill
- R6 — Environment and secret validation hardening
- R7 — Observability baseline
- R8 — Dependency and security baseline refresh

Accepted R hotfixes:
- R8 hotfix — Dependency audit accepts current repo lockfile package names and codex status docs are reconciled with accepted branch history

Accepted S-phase verdicts in the current branch history:
- S1 — Offline LLM topology contract
- S2 — Workflow contract registry
- S3 — Slides plan-first UX contract
- S4 — Slides task event stream and saved-plan retry contract
- S5 — Slides plan editor UI
- S6 — Slides adaptive/template render mode contract
- S7 — Slides source-to-artifact provenance manifest contract
- S8 — Browser-assisted internal evidence capture workflow contract

Next:
- S9 — Optional LiteLLM-compatible gateway and heavy-node integrations

Do not introduce another `S2` or reuse an accepted S number for a different issue.

## R-phase objective

R-phase is operator foundation. It must make the existing deployable stack
verifiable, operable, diagnosable, and safer.

R-phase is not a product expansion phase.

## R-phase order

Codex must not start step N+1 until step N has a committed verdict:

```text
R<N> verdict: ACCEPT
```

Canonical R order:
1. R1 — Full-stack Docker Compose smoke gate
2. R2 — Postgres schema lifecycle and migration preflight
3. R3 — Artifact download UI and export history panel
4. R4 — Restore audit metadata and safer confirmation UX
5. R5 — Operator deployment runbook, backup, and restore drill
6. R6 — Environment and secret validation hardening
7. R7 — Observability baseline
8. R8 — Dependency and security baseline refresh

R is considered complete only when all R verdict commits exist and the current R gates pass. A later R hotfix may be committed after R8 when it fixes a gap in an accepted R gate without expanding scope.

## S-phase objective

S-phase starts only after:

```text
R8 verdict: ACCEPT
```

S-phase deliberately expands product/workflow capability after the operator foundation is stable.

## Reconciled S-phase order

The original planning draft and the accepted branch history diverged after S3. To avoid rewriting accepted history, the canonical sequence is the accepted implementation order below. Older references should be read through the mapping table in the next section.

Accepted / current:
1. S1 — Offline three-server LLM topology and local GigaChat hardening
2. S2 — Workflow contract registry for DOCX/PDF/Slides/Data/Browser/LLM
3. S3 — Slides outline-first / plan-first UX contract
4. S4 — Slides task event stream and saved-plan retry mechanics
5. S5 — Slides plan editor UI
6. S6 — Slides adaptive/template render mode contract
7. S7 — Slides source-to-artifact provenance manifest contract
8. S8 — Browser-assisted internal evidence capture workflow contract

Remaining / rebased:
9. S9 — Optional LiteLLM-compatible gateway and heavy-node integrations
10. S10 — Optional multimodal/visual QA planning layer

## Mapping from the original S planning draft

| Original draft item | Canonical accepted/rebased item | Notes |
| --- | --- | --- |
| S1 — Offline LLM topology / local GigaChat | S1 | unchanged |
| S2 — Workflow contracts | S2 | unchanged |
| S3 — Slides outline-first UX | S3 | unchanged |
| S4 — Adaptive/template deck modes | S6 | implemented after plan editor UI as slides render mode contract |
| S5 — Task event stream and failure recovery | S4 | implemented earlier as slides task events and saved-plan retry mechanics |
| S6 — Source-to-artifact provenance | S7 | implemented as slides provenance manifest contract |
| S7 — Browser-assisted internal workflows | S8 | accepted as browser-assisted internal evidence capture workflow contract |
| S8 — Optional LiteLLM-compatible gateway and heavy-node integrations | S9 | shifted by browser-assisted rebasing |
| S9 — Optional multimodal/visual QA planning layer | S10 | shifted by browser-assisted rebasing |

## S9 target: optional LiteLLM-compatible gateway and heavy-node integrations

S9 must be a contract and diagnostics step first, not a runtime rewrite.

Scope for S9:
- keep direct local GigaChat as default production LLM transport;
- document optional LiteLLM-compatible gateway on Server 2;
- define configuration and routing contracts for `direct_gigachat` vs `litellm_gateway`;
- add no-network diagnostics by default, with any endpoint probe behind an explicit flag;
- integrate S9 checks into the production readiness gate only after focused S9 tests pass.

Non-goals for S9:
- do not replace GigaChat as the default production LLM;
- do not make LiteLLM mandatory;
- do not introduce internet dependency;
- do not build heavy OCR/rerank/visual-QA runtime yet;
- do not silently route prompts through a gateway when direct GigaChat is configured.

## Product direction inherited from Kimi research

Use Kimi-derived ideas as workflow patterns, not as cloud dependencies:
- outline-first workflows;
- editable plan before generation;
- adaptive/template Slides modes;
- retry from saved plan;
- tool/workflow contracts;
- approval boundaries;
- long-running task event stream;
- visual/multimodal QA later.

Do not introduce dependence on Kimi cloud, internet runtime, or external services.


## S10 target: optional multimodal/visual QA planning layer
S10 must be a planning contract first, not a runtime implementation.

Scope for S10:
- define visual QA plan manifests for generated artifacts;
- keep all visual QA runtime optional and future-facing;
- store artifact references and planned checks, not raw screenshots, raw pixels, or raw OCR text;
- keep external visual APIs and internet dependency out of the default/offline path;
- integrate S10 checks into the production readiness gate only after focused S10 tests pass.

Non-goals for S10:
- do not implement OCR, screenshot analysis, or multimodal model runtime;
- do not require Server 2 heavy-node modules;
- do not send artifacts to cloud visual APIs;
- do not bypass operator review for visual QA findings.
