# AGENTS.md

## Project

Build **KW Studio**: an AI workspace for knowledge work that turns user files and natural-language tasks into finished work products.

The MVP is a **modular monolith**, not a microservice platform.

Primary MVP outcomes:
- edited `.docx`
- summarized `.pdf`
- generated `.pptx`
- spreadsheet/data analysis with charts and downloadable artifacts

## Product boundaries

### In scope for MVP
- Chat-based workspace
- File upload and artifact download
- DOCX workflows
- PDF workflows
- Slides generation
- Spreadsheet / CSV data analysis
- Python execution through a controlled runtime
- Background task execution
- Basic session/task/artifact persistence

### Out of scope for MVP
- Full autonomous browser agent as a user-facing feature
- Realtime collaboration
- Broad file-format zoo
- General-purpose app builder UI
- Multi-tenant enterprise controls
- Complex RBAC beyond basic authentication

## Architecture rules

- Keep the system as a **modular monolith** for v1.
- Keep business services separate from runtime code.
- Keep FastAPI endpoints thin.
- Do not introduce hidden side effects at import time.
- Browser runtime is **internal-only** in MVP.
- Prefer adapters and service boundaries over direct cross-module calls.
- New code should fit the repository structure described in `README.md` and `docs/product-spec.md`.

## Coding rules

### Python
- Use type hints in new code.
- Prefer explicit dependency injection over globals.
- Use `logging`, not `print`.
- Avoid broad `except Exception` unless you re-raise or log with context.
- Use Pydantic models for external API contracts.
- Keep runtime components restart-safe and testable.

### Frontend
- Use React / Next.js with clear feature boundaries.
- Keep API calls in dedicated client modules.
- Avoid business logic inside UI components.
- Prefer small composable components.

### General
- Prefer small, reviewable patches.
- Add tests for every non-trivial change.
- Update docs when architecture, APIs, or setup change.
- Preserve backward compatibility unless the task explicitly allows breaking changes.

## Required checks

When changing backend code:
- `pytest -q`

When changing frontend code:
- `npm run lint`
- `npm run build`

When changing runtime code:
- run relevant smoke tests
- explain what was tested

## MVP definition of done

A task is done only if:
- the code builds or runs in the intended environment
- relevant tests pass
- the behavior matches the acceptance criteria
- docs are updated when needed
