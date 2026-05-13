# XLSX Validation

XLSX validation ensures workbook artifacts are safe, inspectable, and traceable.

## Required checks

- Workbook file exists and is non-empty.
- Workbook opens with the configured XLSX library.
- Sheet names and dimensions are recorded.
- Formula cells are inventoried.
- Generated workbooks are reopened after writing.
- Table previews reference sheet and range.
- Chart/table artifacts reference source data.

## Compatibility principles

- Avoid silently introducing formulas that are unavailable in the target Excel compatibility mode.
- Do not destroy existing sheets, formulas, or formatting unless the user explicitly requested it.
- Report unsupported workbook features instead of hiding them.

## Relationship to Slides

Slides may consume XLSX-derived tables and charts. When that happens, slide citations and evidence manifests should reference workbook, sheet, and range.
