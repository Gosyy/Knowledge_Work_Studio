# XLSX / Excel Workflow

The XLSX workflow is a mandatory first-class KW Studio workflow, equal in priority to DOCX, PDF, Slides, Python analysis, and browser-assisted evidence.

## Goals

- Read `.xlsx` and compatible tabular inputs.
- Inspect workbooks, sheets, dimensions, tables, formulas, and chart inputs.
- Validate workbook integrity and formula structure.
- Produce analysis reports and optional generated or cleaned workbooks.
- Feed tables and charts into Slides with source-range provenance.

## Expected artifacts

- `workbook_manifest.json`.
- `xlsx_quality_report.json`.
- `formula_inventory.json`.
- `table_previews/*.csv`.
- Optional generated `.xlsx` workbook.
- `source_evidence_manifest.json`.

## Quality checks

- Workbook opens with the configured XLSX engine.
- Sheets are inventoried.
- Formula cells are counted and reported.
- Generated workbooks open after writing.
- Chart/table outputs reference source workbook, sheet, and range.
- No destructive edits are made unless explicitly requested.

## Product note

Excel support must not be treated as a future optional feature. It is part of the core KW Studio product identity because knowledge-work output commonly depends on spreadsheets, workbook calculations, charts, and table evidence.

## KR-5A inspect runtime

KR-5A introduces the first concrete XLSX / CSV inspect runtime in:

```text
backend/app/services/xlsx_service/
scripts/kw_xlsx_inspect_workflow_check.py
```

The inspect runtime is intentionally deterministic, offline-ready, and non-destructive. It reads workbook package XML directly, inventories sheet metadata and formulas, exports table previews, and builds an artifact bundle without modifying the source workbook.

KR-5A required bundle outputs are:

```text
workbook.xlsx or workbook.csv
workbook_manifest.json
xlsx_analysis_report.json
formula_inventory.json
table_previews/*.csv
source_evidence_manifest.json
artifact_manifest.json
quality_report.json
```

The workflow is inspect-only at KR-5A. It does not repair formulas, create charts, write pivot summaries, or modify workbooks. Those capabilities belong to later XLSX phases after the inspect and validation contracts are stable.
