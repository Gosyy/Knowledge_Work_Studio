# KR-2C Stage Checker Dependency Inventory

KR-2C maps the remaining direct dependencies from legacy stage checker scripts and stage smoke tests to `docs/codex/*.md`.

This step is intentionally diagnostic. It does not move, delete, or rename files.

## Why this exists

KR-1B proved that physically moving `docs/codex/*.md` too early breaks the full runner, because many old checker scripts and tests still read those files directly. KR-1B-R2 therefore marked `docs/codex` as deprecated development history but left it in place.

KR-2C gives the next required map:

- which checker scripts read `docs/codex` directly;
- which tests read `docs/codex` directly;
- which tests invoke checker scripts;
- which files block physical documentation archive;
- which product-level test or checker should replace each dependency.

## Product direction

The replacement direction remains:

- `backend/tests/workflows/` for DOCX, PDF, XLSX, Slides, Python analysis, and Browser evidence workflows;
- `backend/tests/quality/` for artifact bundle, provenance, source grounding, XLSX validation, and render QA;
- `backend/tests/integrations/` for storage, database, metadata, LLM topology, and path portability;
- `backend/tests/operators/` for log archive, production readiness, diagnostics, and deployment checks.

## Acceptance criteria

KR-2C is accepted when:

1. the inventory script runs from arbitrary `--repo-root`;
2. it emits JSON and Markdown reports;
3. it identifies direct `docs/codex` dependencies;
4. it produces a rewrite order;
5. it does not delete or move legacy docs;
6. full runner and Docker smoke pass after commit.

## What KR-2C does not do

KR-2C does not rewrite stage tests yet. That starts in KR-2D/KR-2E/KR-2F.
