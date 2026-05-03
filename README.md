# KW Studio

KW Studio is an offline/intranet, artifact-first knowledge-work studio.
It turns user files and natural-language tasks into downloadable, versioned,
and auditable work products such as edited documents, presentation decks,
source-grounded summaries, and data-analysis artifacts.

## Current canonical planning

The accepted R/S checkpoint lives on branch `6_Stage_R` at commit `d034314`.
After that checkpoint, development continues in the Runtime Foundation phase.

Start with these documents:

- `docs/codex/README.md`
- `docs/codex/R_AND_S_MASTER_PLAN.md`
- `docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md`
- `docs/codex/CODEX_OPERATING_RULES.md`
- `docs/codex/ACCEPTANCE_GATES.md`
- `docs/codex/OFFLINE_LLM_TOPOLOGY.md`

Historical bootstrap prompt packs and early roadmap stubs were removed during
RF0 repository hygiene so new work uses the canonical `docs/codex/` plan.

## Architecture identity

KW Studio v1 remains:

- modular monolith;
- offline/intranet first;
- artifact-first;
- provenance-first;
- operator-gated;
- local GigaChat-first for production LLM use.

Do not turn it into a cloud-first framework, a microservice platform, a broad
file-format zoo, or a general autonomous browser-agent product.

## Quick local start

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
make create-dirs
make test
make run
```

Health check:

- `http://localhost:8000/health`

## Operator checks

For full local verification, use the project runner maintained outside the repo:

```bash
/home/su4ka/Загрузки/run_kws_full_tests_with_proxy.sh
```

The runner name includes `proxy` historically. It also works without a proxy
when `.proxy.env` is absent and proxy environment variables are unset.
