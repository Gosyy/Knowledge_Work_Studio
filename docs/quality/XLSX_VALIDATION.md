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

## KR-5A inspect validation contract

KR-5A makes XLSX inspection a runtime capability rather than only a documentation promise. The validation guardrail lives in:

```text
scripts/kw_xlsx_inspect_workflow_check.py
```

The guardrail must confirm that:

```text
the sample workbook opens;
sheet metadata is extracted;
formula inventory is written;
table previews are written as CSV artifacts;
source_evidence_manifest.json maps sheets/ranges to previews;
artifact_manifest.json lists the generated bundle files;
quality_report.json fails closed when required inspection data is missing;
destructive_edit_performed remains false for inspect-only workflows.
```

If the workbook is malformed, the workflow must return a failed inspection result with explicit errors instead of pretending success.

## KR-5B bundle validation hardening

KR-5B adds a fail-closed validation layer for the XLSX inspect artifact bundle.
The checker is:

```text
scripts/kw_xlsx_validation_bundle_check.py
```

KR-5B validation confirms:

```text
required artifacts are present;
artifact_manifest.json lists all required artifacts;
manifest size and sha256 values match the actual artifacts;
artifact_manifest.json uses an explicit self_reference entry instead of a fake self-hash;
source workbook hash is traceable from workbook_manifest.json;
formula inventory agrees with xlsx_analysis_report.json;
formula records include sheet name, cell reference, formula text, and worksheet file;
table previews exist, are non-empty, and are referenced from source_evidence_manifest.json;
quality_report.json remains ready and non-destructive;
corrupt or incomplete bundles fail closed.
```

This is still not full Excel parity. It hardens inspection output so later XLSX workflows can safely consume the artifact bundle.
