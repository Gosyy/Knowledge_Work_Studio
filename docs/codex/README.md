# KW Studio Codex Documentation Pack

This pack is the operating documentation for Codex work on KW Studio after the R-phase operator foundation and the first S-phase product/workflow contracts.

Current verified branch state:
- branch: `6_Stage_R`
- R-phase status: `R1` through `R8` accepted
- latest accepted S verdict represented by this source archive: `S7 verdict: ACCEPT`
- current canonical S sequence: the implementation-history sequence in `R_AND_S_MASTER_PLAN.md`
- next planning action: continue from the reconciled S sequence; do not re-use old S numbers with different meanings

One-line product identity:

KW Studio is an offline/intranet artifact-first knowledge-work studio for:
DOCX + PDF + Slides + Python + Browser-assisted workflows.

Default production LLM: local GigaChat on Server 3.
Optional gateway: LiteLLM-compatible gateway on Server 2.
Optional fallback/dev backend: Ollama/local models on Server 2.

Documents:
- `R_AND_S_MASTER_PLAN.md`
- `CODEX_OPERATING_RULES.md`
- `R_PHASE_CODEX_PROMPTS.md`
- `S_PHASE_CODEX_PROMPTS.md`
- `OFFLINE_LLM_TOPOLOGY.md`
- `PATCH_SCRIPT_TEMPLATE.md`
- `ACCEPTANCE_GATES.md`

Important status note:
The original S plan used `S7` for browser-assisted internal workflows. The accepted branch history uses `S7` for the slides provenance manifest contract. The canonical plan now preserves the accepted history and rebases browser-assisted internal workflows to the next unclaimed S slot instead of renaming existing accepted commits.
