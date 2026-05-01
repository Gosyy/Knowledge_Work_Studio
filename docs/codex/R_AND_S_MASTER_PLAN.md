# KW Studio R and S Master Plan

## Product identity

KW Studio is an artifact-first offline/intranet knowledge-work studio. It turns user files and natural-language tasks into finished, downloadable, versioned, and auditable work products:

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
- S9 — Optional LiteLLM-compatible gateway and heavy-node integrations
- S10 — Optional multimodal/visual QA planning layer

Post-S10 planning checkpoint:

- `S1` through `S10` are accepted.
- Latest accepted S verdict: `S10 verdict: ACCEPT`.
- No canonical `S11` task is allocated yet.
- Choose the next phase/branch and write its scope before assigning another S number.

Do not introduce another `S2`, duplicate a verdict intentionally, or reuse an accepted S number for a different issue.

## R-phase objective

R-phase is operator foundation. It must make the existing deployable stack verifiable, operable, diagnosable, and safer.

R-phase is not a product expansion phase.

## R-phase order

Codex must not start step N+1 until step N has a committed verdict:

```text
R verdict: ACCEPT
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
9. S9 — Optional LiteLLM-compatible gateway and heavy-node integrations
10. S10 — Optional multimodal/visual QA planning layer

Remaining / rebased:

- None allocated in this document.
- Do not allocate `S11` without a new planning checkpoint.

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

## Accepted S9 summary: optional LiteLLM-compatible gateway and heavy-node integrations

S9 is a contract and diagnostics step, not a runtime rewrite.

Accepted S9 scope:

- keep direct local GigaChat as default production LLM transport;
- document optional LiteLLM-compatible gateway on Server 2;
- define configuration and routing contracts for `direct_gigachat` vs `litellm_gateway`;
- add no-network diagnostics by default, with any endpoint probe behind an explicit flag;
- integrate S9 checks into the production readiness gate after focused S9 tests pass.

S9 non-goals:

- do not replace GigaChat as the default production LLM;
- do not make LiteLLM mandatory;
- do not introduce internet dependency;
- do not build heavy OCR/rerank/visual-QA runtime;
- do not silently route prompts through a gateway when direct GigaChat is configured.

## Accepted S10 summary: optional multimodal/visual QA planning layer

S10 is a planning-only visual QA contract. It does not implement OCR, vision-model inference, screenshot parsing, or an external visual API.

Accepted S10 scope:

- define a visual QA planning manifest for slides and artifact workflows;
- require artifact references instead of raw screenshots, raw pixels, or raw OCR text;
- keep visual QA offline/intranet-ready;
- mark Server 2 heavy runtime as optional future infrastructure;
- integrate visual QA planning checks into production readiness;
- preserve operator review and provenance linkage.

S10 non-goals:

- no OCR runtime;
- no multimodal model runtime;
- no external/cloud visual QA service;
- no autonomous browser expansion;
- no automatic rejection of generated artifacts without operator review.

## Post-S10 planning rules

Before starting another S-numbered task:

1. Decide whether the next work belongs in `6_Stage_R` or a new branch.
2. Decide whether the next sequence is `S11` or a new named phase.
3. Write a docs-only planning checkpoint before implementation.
4. Keep the accepted-history mapping intact.
5. Keep using the full post-step gate:
   - targeted tests;
   - backend tests;
   - frontend build;
   - frontend E2E smoke;
   - production readiness gate;
   - GitHub push and verification;
   - Docker check-only always;
   - Docker runtime smoke with `--skip-build` when images are available;
   - full Docker build only when npm registry/cache access is available.

## Product direction inherited from Kimi research

Use Kimi-derived ideas as workflow patterns, not as cloud dependencies:

- outline-first workflows;
- editable plan before generation;
- adaptive/template Slides modes;
- retry from saved plan;
- tool/workflow contracts;
- approval boundaries;
- long-running task event stream;
- visual/multimodal QA planning and operator review.

Do not introduce dependence on Kimi cloud, internet runtime, or external services.
