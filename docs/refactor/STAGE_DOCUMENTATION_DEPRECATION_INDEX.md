# Stage Documentation Deprecation Index

KR-1B-R2 intentionally does **not** move `docs/codex` files. The previous physical archive attempt proved that many legacy smoke tests and checker scripts still read stage documents directly from their old paths.

`docs/codex remains temporarily for legacy tests/checkers` until **KR-2** rewrites those stage-specific checks into product workflow and quality tests.

## Current rule

Canonical product docs are the source of truth for the product:

- `docs/product/PRODUCT_VISION.md`
- `docs/product/USER_WORKFLOWS.md`
- `docs/product/ARTIFACT_MODEL.md`
- `docs/workflows/DOCX_WORKFLOW.md`
- `docs/workflows/PDF_WORKFLOW.md`
- `docs/workflows/XLSX_WORKFLOW.md`
- `docs/workflows/SLIDES_WORKFLOW.md`
- `docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md`
- `docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md`
- `docs/quality/QUALITY_GATES.md`
- `docs/quality/XLSX_VALIDATION.md`
- `docs/quality/RENDER_AND_VISUAL_QA.md`
- `docs/operators/LOCAL_DEVELOPMENT.md`
- `docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md`

`docs/codex` is deprecated development history. New product documentation must not be added there.

## Current continuation checkpoint

The active continuation checkpoint is maintained in:

```text
docs/refactor/KR_CURRENT_CONTINUATION_PLAN.md
```

That document supersedes older migration anchors that stopped at KR-2A or treated KR-2B as unresolved. The current cleanup direction remains conservative: product replacements first, dependency retirement second, physical archive/delete only after active references are cleared.

## Why physical archive is blocked

The failed KR-1B attempt showed that moving stage documentation before test cleanup breaks the test suite. Some legacy checker scripts assert exact `docs/codex/*.md` paths. Moving those files first creates a noisy failure mode and hides the real cleanup objective.

The safe order is:

1. KR-1B-R2: mark stage docs deprecated without moving them.
2. KR-2: rewrite/remove stage-specific tests and checker scripts.
3. Later KR cleanup: physically archive or delete obsolete stage documents in controlled batches.

## Product workflow target

The active project direction is:

- DOCX workflow
- PDF workflow
- XLSX/Excel workflow
- Slides workflow
- Python analysis workflow
- Browser evidence workflow

All future documentation and tests should describe these product capabilities instead of historical stage names.
