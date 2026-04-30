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

Accepted:
- R1 — full-stack Docker Compose smoke gate

Next:
- R2 — Postgres schema lifecycle and migration preflight

## R-phase objective

R-phase is operator foundation. It must make the existing deployable stack
verifiable, operable, diagnosable, and safer.

R-phase is not a product expansion phase.

## R-phase order

Codex must not start step N+1 until step N has a committed verdict:

```text
R<N> verdict: ACCEPT
```

Order:
1. R2 — Postgres schema lifecycle and migration preflight
2. R3 — Artifact download UI and export history panel
3. R4 — Restore audit metadata and safer confirmation UX
4. R5 — Operator deployment runbook, backup, and restore drill
5. R6 — Environment and secret validation hardening
6. R7 — Observability baseline
7. R8 — Dependency and security baseline refresh

## S-phase objective

S-phase starts only after:

```text
R8 verdict: ACCEPT
```

Recommended S-phase order:
1. S1 — Offline three-server LLM topology docs and direct local GigaChat hardening
2. S2 — Workflow contracts for DOCX/PDF/Slides/Data/Browser/LLM
3. S3 — Slides outline-first UX and editable plan approval
4. S4 — Adaptive/template deck generation modes
5. S5 — Task event stream and failure recovery
6. S6 — Source-to-artifact provenance
7. S7 — Browser-assisted internal workflows
8. S8 — Optional LiteLLM-compatible gateway and heavy-node integrations
9. S9 — Optional multimodal/visual QA planning layer

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
