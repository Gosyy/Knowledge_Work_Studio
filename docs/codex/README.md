# KW Studio Codex Documentation Pack

This pack is the operating documentation for Codex work on KW Studio after the R-phase operator foundation and the accepted S-phase product/workflow contract sequence.

## Current verified branch state

- branch: `6_Stage_R`
- R-phase status: `R1` through `R8` accepted
- R8 hotfix status: `R8 hotfix dependency audit and reconcile codex status docs` accepted
- S-phase status: `S1` through `S10` accepted
- latest accepted S verdict: `S10 verdict: ACCEPT`
- Post-S10 planning checkpoint: choose the next phase/branch before assigning another S number
- no canonical `S11` task is allocated yet

## Product identity

KW Studio is an offline/intranet artifact-first knowledge-work studio for:

- DOCX workflows
- PDF workflows
- Slides workflows
- Python/data workflows
- Browser-assisted internal evidence workflows
- Offline/local LLM-assisted workflows

Default production LLM: local GigaChat on Server 3.

Optional gateway: LiteLLM-compatible gateway on Server 2.

Optional fallback/dev backend: Ollama/local models on Server 2.

## Documents

- `R_AND_S_MASTER_PLAN.md`
- `CODEX_OPERATING_RULES.md`
- `R_PHASE_CODEX_PROMPTS.md`
- `S_PHASE_CODEX_PROMPTS.md`
- `OFFLINE_LLM_TOPOLOGY.md`
- `PATCH_SCRIPT_TEMPLATE.md`
- `ACCEPTANCE_GATES.md`

## Important status note

The original S plan and the accepted branch history diverged after S3. The canonical plan preserves accepted history instead of renaming existing accepted commits.

Accepted branch history is now:

1. `S1` — Offline LLM topology contract
2. `S2` — Workflow contract registry
3. `S3` — Slides plan-first UX contract
4. `S4` — Slides task event stream and saved-plan retry contract
5. `S5` — Slides plan editor UI
6. `S6` — Slides adaptive/template render mode contract
7. `S7` — Slides source-to-artifact provenance manifest contract
8. `S8` — Browser-assisted internal evidence capture workflow contract
9. `S9` — Optional LiteLLM-compatible gateway and heavy-node integrations
10. `S10` — Optional multimodal/visual QA planning layer

Do not reuse any accepted S number for a different issue. Do not create `S11` until a new planning document or docs-only checkpoint defines its scope.
