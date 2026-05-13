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
