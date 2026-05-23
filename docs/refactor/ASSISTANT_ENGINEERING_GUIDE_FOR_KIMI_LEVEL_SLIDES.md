# Assistant engineering guide for Kimi-level Slides work

## Purpose

This guide defines how an assistant, Codex-like agent, or future coding assistant must write production-grade KW Studio code for the KR-7 Kimi-level Slides roadmap.

The goal is not to maximize lines of code. The goal is to build correct, maintainable, testable, offline-safe product functionality that produces useful artifacts.

## Mandatory reading before Slides KR-7 work

Read in order:

1. `AGENTS.md`
2. `README.md`
3. `docs/refactor/PROJECT_MIGRATION_HANDOFF.md`
4. `docs/refactor/CODEX_PROJECT_BRIEFING.md`
5. `docs/refactor/SLIDES_KIMI_LEVEL_GAP_AUDIT.md`
6. `docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md`
7. `docs/refactor/TEST_PORTFOLIO_RATIONALIZATION_PLAN.md`
8. relevant code and tests for the module being changed.

## Senior engineering rules

Do not:

- write prompt-only hacks for architectural problems;
- weaken tests to make a patch pass;
- hide product failures behind fallback;
- add generated images when the roadmap forbids them;
- create charts without data source refs;
- add local small LLMs, Ollama or arbitrary model selectors;
- claim Kimi-level quality before quality gates pass;
- bypass API contracts to make frontend work quickly;
- copy external code without license/dependency review;
- introduce broad refactors unrelated to the phase;
- ignore actual local state before patching.

Do:

- produce typed contracts first;
- validate every external input;
- fail closed on unsupported professional claims;
- keep provenance and quality artifacts first-class;
- write tests at the right level, not the maximum possible number;
- preserve backwards compatibility unless a cleanup phase explicitly removes it;
- document behavior changes in the handoff;
- use project-resident runners for acceptance.

## External repositories and how to use them

External repositories may be used as references, not as unchecked dependencies. If a future assistant needs deeper analysis, ask the operator to download the source and place it beside the project or under a controlled `external_research/` or `reference_materials/` directory outside product runtime.

### PptxGenJS

Reference:

- https://github.com/gitbrent/PptxGenJS
- https://gitbrent.github.io/PptxGenJS/
- https://gitbrent.github.io/PptxGenJS/docs/api-charts/

Recommended use:

- renderer worker for native PPTX charts, tables, shapes and images;
- Node-side deterministic render CLI;
- native chart rendering from real numeric data;
- custom slide masters and 16:9 layouts.

Do not:

- move presentation truth to frontend;
- render fake chart values;
- bypass backend artifact/provenance contracts.

### PPTAgent

Reference:

- https://github.com/icip-cas/PPTAgent

Recommended use:

- learn concepts: reference presentations, slide functional types, content schema, edit actions, content/design/coherence evaluation.

Do not:

- claim PPTAgent parity;
- copy evaluation code without understanding licensing and dependencies.

### PresentAgent-2

Reference:

- https://github.com/AIGeeksGroup/PresentAgent-2

Recommended use:

- study pipeline architecture: refine query, gather/extract materials, plan structure, generate slides, compose output;
- adapt research to KW Studio offline source extraction and evidence retrieval.

Do not:

- introduce public web search in offline production;
- import cloud dependencies without explicit acceptance.

### Mermaid

Reference:

- https://mermaid.js.org/

Recommended use:

- diagram specification/preview DSL;
- debug representation of flowchart/roadmap/process blocks;
- optional UI preview.

Do not:

- use screenshot Mermaid output as final native PPTX diagram unless explicitly accepted as fallback;
- call static Mermaid images native editable components.

### React Flow / xyflow

Reference:

- https://reactflow.dev/
- https://github.com/xyflow/xyflow

Recommended use:

- frontend editor for node-based diagrams and workflows;
- UI editing for process flows, architecture diagrams, decision trees, roadmap graphs.

Do not:

- make React Flow the backend source of truth;
- export only screenshots when native PPTX components are required.

### Slidev

Reference:

- https://github.com/slidevjs/slidev
- https://sli.dev/guide/
- https://sli.dev/guide/exporting

Recommended use:

- learn from Markdown-first authoring, themes, layouts, web preview, export worker concepts.

Do not:

- replace KW Studio artifact/provenance workflow with Slidev;
- use Slidev export as the main PPTX path without strict compatibility and QA review.

### AIFixed

Reference material:

- operator-supplied `AIFixed-main.zip` archive.

Useful UI ideas:

- React/MUI presentation editor surfaces;
- block editing;
- DnD slide/block ordering;
- theme selector;
- chart and table editors;
- PptxGenJS export mapping concepts;
- slide thumbnails and editor workflows.

Do not import:

- AIFixed backend as runtime architecture;
- model manager, local embeddings, CrossEncoder or Qdrant assumptions;
- arbitrary/default model selection;
- frontend-side generation as source of truth;
- hardcoded model names;
- RAG pipeline that violates KW Studio offline/GigaChat-only policy.

## External source download policy

If the assistant cannot safely decide from docs alone, it must ask the operator to provide the source archive or permission to clone into a reference-only directory. Use external source only for study and architecture extraction unless a separate license review allows copying.

Recommended local layout:

```text
reference_materials/
  PptxGenJS/
  PPTAgent/
  PresentAgent-2/
  slidev/
  xyflow/
  AIFixed-main/
```

This directory must not become product runtime input and should not be included in Docker images unless explicitly approved.

## Code quality definition

Good code in this phase must be:

- typed;
- contract-driven;
- tested at the right level;
- profile-neutral;
- offline-safe;
- provenance-aware;
- quality-gated;
- maintainable by another senior engineer;
- reversible by commit;
- documented when behavior changes.

Bad code includes:

- broad string patching;
- magic constants without contract;
- pseudo charts;
- decorative image placeholders;
- raw prompt/response logging;
- secret leakage;
- hidden network calls;
- hidden model downloads;
- temporary production flags;
- unbounded retries;
- tests that assert implementation trivia instead of product contracts.

## Required assistant output for each KR-7 patch

Before code:

1. summarize actual repo state;
2. summarize relevant docs read;
3. identify contracts affected;
4. identify tests to run;
5. state non-goals.

After code:

1. list files changed;
2. explain product effect;
3. list targeted tests and results;
4. report risks;
5. state whether full runner/Docker smoke/push were done;
6. never claim ACCEPT without evidence logs.

<!-- LOCAL_FULL_HISTORY_ENGINEERING_REQUIREMENT -->

## Local full-history engineering requirement

For KR-7 and all future code work, an assistant must not write or repair code from snippets alone. It must work against an actual local checkout or mirror-derived clone with full Git history.

Required preflight for code patches:

```bash
git rev-parse --is-shallow-repository
git status --short --branch
git log --oneline --decorate --graph -20
git branch -vv
git remote -v
```

If no such checkout is available, ask the operator for a full-history clone or bare mirror archive. Do not approximate the patch from GitHub file views. Do not issue a weak repair-runner before reproducing the failure and testing the fix locally.

<!-- KR7_VENV_ONLY_DEV_RULE -->

## Virtual environment requirement

Use the project `.venv` for all local analysis, code generation support, patch validation and tests.

Required preflight:

```bash
cd <project-root>
test -d .venv || python3 -m venv .venv
. .venv/bin/activate
python -c "import sys; print(sys.executable)"
python -m pip --version
python -m pytest --version
```

The printed Python executable must point inside the project `.venv`. If dependencies are missing, install them into `.venv` through the project dependency files and resolve the failure before continuing. Do not silently fall back to `/usr/bin/python`, do not ignore warnings, and do not treat a system-Python run as valid evidence for acceptance.
