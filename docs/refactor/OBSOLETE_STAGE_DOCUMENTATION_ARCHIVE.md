# KR-1B obsolete stage documentation archive

KR-1B is the first cleanup patch that changes the repository tree after the
KR-0 inventory and policy stages.

It does not delete historical knowledge. It moves stage-specific development
documentation out of the active documentation tree and into an archive area:

```text
docs/archive/development-history/
```

The product-facing documentation introduced by KR-1A remains the active entry
point for the project:

```text
docs/product/
docs/architecture/
docs/workflows/
docs/quality/
docs/operators/
```

## Why this exists

KW Studio has accumulated many documents that describe how individual stages,
patches, review packets, and release decisions were produced. Those files were
useful during development, but they are not the product documentation a new
operator or developer should read first.

The product direction is now stable:

```text
DOCX + PDF + XLSX/Excel + Slides + Python analysis + Browser-assisted workflows
```

The active documentation should describe this product and its workflow
contracts. Stage documents should remain available only as historical evidence.

## What KR-1B archives

The archive tool reads a KR-0B cleanup policy report and moves only entries that
match all of these conditions:

```text
kind = doc
action = archive
path starts with docs/
```

It intentionally does not move tests, scripts, source code, fixtures, or active
product documentation. Those are handled by later KR patches.

## What KR-1B does not do

KR-1B does not:

- remove source code;
- remove tests;
- rename KQ/S/P/RC service modules;
- implement XLSX processing;
- claim Kimi-level quality;
- change runtime behavior of workflow generation.

## Production readiness compatibility

Older production-readiness checks still refer to some legacy documentation by
its original path. KR-1B updates the readiness gate so a required Markdown file
is accepted in either location:

```text
docs/codex/EXAMPLE.md
docs/archive/development-history/codex/EXAMPLE.md
```

This keeps the historical evidence available while allowing the active docs tree
to become product-oriented.

## Follow-up patches

KR-1B prepares the repository for the next cleanup steps:

```text
KR-2A/KR-2B: convert stage-specific tests to product tests.
KR-3A/KR-3B: remove profile/path/branch/commit assumptions.
KR-4A: consolidate workflow contracts.
KR-5A: make XLSX a first-class executable workflow.
```

## Operator usage

The archive operation is intentionally explicit:

```bash
python3 scripts/kw_archive_obsolete_stage_docs.py \
  --repo-root . \
  --policy-zip logs/kr0b-cleanup-policy-report.zip \
  --output-dir logs/kr1b-archive-report \
  --execute \
  --json

python3 scripts/kw_archived_stage_docs_check.py \
  --repo-root . \
  --policy-zip logs/kr0b-cleanup-policy-report.zip \
  --output-dir logs/kr1b-archive-check \
  --require-ready \
  --json
```

Running without `--execute` performs a dry run.
