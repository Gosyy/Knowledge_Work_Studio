# KW Studio Codex Documentation Pack

This pack is the operating documentation for Codex work on KW Studio after the
accepted R-phase operator foundation and accepted S-phase product/workflow
contract sequence.

## Current verified branch state

- accepted checkpoint branch: `6_Stage_R`
- accepted checkpoint commit: `d034314` (`Docs mark S10 accepted and set post-S10 checkpoint`)
- R-phase status: `R1` through `R8` accepted
- R8 hotfix status: accepted
- S-phase status: `S1` through `S10` accepted
- latest accepted S verdict: `S10 verdict: ACCEPT`
- canonical `S11`: not allocated
- next development branch: `7_Runtime_Foundation`
- next phase: Runtime Foundation / RF

Do not create `S11` unless a later docs-only checkpoint explicitly assigns that
scope. The Runtime Foundation phase is a new named phase, not an S-number
continuation.

## Product identity

KW Studio is an offline/intranet artifact-first knowledge-work studio for:

- DOCX workflows;
- PDF workflows;
- Slides workflows;
- Python/data workflows;
- browser-assisted internal evidence workflows;
- offline/local LLM-assisted workflows.

Default production LLM: local GigaChat on Server 3. Optional gateway:
LiteLLM-compatible gateway on Server 2. Optional fallback/dev backend:
Ollama/local models on Server 2.

## Canonical documents

- `R_AND_S_MASTER_PLAN.md`
- `RUNTIME_FOUNDATION_PHASE_PLAN.md`
- `CODEX_OPERATING_RULES.md`
- `R_PHASE_CODEX_PROMPTS.md`
- `S_PHASE_CODEX_PROMPTS.md`
- `OFFLINE_LLM_TOPOLOGY.md`
- `PATCH_SCRIPT_TEMPLATE.md`
- `ACCEPTANCE_GATES.md`

## Runtime Foundation order

Runtime Foundation starts after the accepted post-S10 checkpoint.

1. `RF0` — Runtime Foundation phase checkpoint and repository hygiene
2. `RF1` — Offline dependency and Docker reproducibility hardening
3. `RF2` — Slides runtime continuation
4. `RF3` — Real document ingestion for DOCX and PDF
5. `RF4` — Local GigaChat integration hardening

RF0 is docs/hygiene-only. Runtime implementation starts only after RF0 is
accepted and a real deploy/test baseline is reviewed.

## Important accepted-history note

The original S plan and the accepted branch history diverged after S3. The
canonical plan preserves accepted history instead of renaming existing accepted
commits. Accepted branch history is now:

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

Do not reuse any accepted S number for a different issue.
