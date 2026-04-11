# NEXT_PHASE_PROMPTS.md

## Prompt A1 — Persistent repositories

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md

Implement Issue A1 only.

Goals:
- replace in-memory repositories with persistent implementations
- keep repository interfaces stable where possible
- preserve current API behavior
- keep the modular monolith architecture intact

Constraints:
- do not rewrite unrelated services
- do not touch frontend
- do not introduce unnecessary infrastructure complexity
- add tests for repository persistence behavior

Acceptance criteria:
- sessions persist across restart
- tasks persist across restart
- artifacts persist across restart
- uploaded file metadata persists across restart
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend
```

## Prompt A2 — DB bootstrap and migration baseline

```text
Work from the repository root.

Read these files first:
- AGENTS.md
- docs/product-spec.md
- docs/roadmap.md

Implement Issue A2 only.

Goals:
- add database settings wiring
- add DB initialization path
- add a migration baseline structure
- document local DB startup and migration flow

Constraints:
- keep the solution simple
- do not overengineer migrations
- preserve current app startup behavior
- keep tests passing

Acceptance criteria:
- DB bootstrap exists
- migration baseline exists
- local DB setup is documented
- pytest -q passes
- python -m compileall backend passes

Run these checks:
- pytest -q
- python -m compileall backend
```
