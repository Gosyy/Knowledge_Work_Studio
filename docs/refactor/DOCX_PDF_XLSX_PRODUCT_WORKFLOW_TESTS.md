# KR-2F DOCX/PDF/XLSX Product Workflow Tests

KR-2F adds first-class product-level tests for DOCX, PDF, and XLSX/Excel workflows.

## Purpose

The KR plan requires DOCX, PDF, and XLSX/Excel to be mandatory product pillars. DOCX and PDF already had legacy RF3 runtime tests, but the test names and assertions were still tied to a historical stage. XLSX/Excel had canonical documentation, but it needed a product-level validation contract.

KR-2F adds product-named coverage without deleting legacy RF tests.

## Added product tests

```text
backend/tests/workflows/test_docx_workflow_product_contract.py
backend/tests/workflows/test_pdf_workflow_product_contract.py
backend/tests/workflows/test_xlsx_workflow_product_contract.py
backend/tests/quality/test_xlsx_validation_product_contract.py
backend/tests/smoke/test_docx_pdf_xlsx_product_workflows.py
```

## Added checker

```text
scripts/kw_docx_pdf_xlsx_product_workflows_check.py
```

## DOCX contract

The DOCX product test verifies:

- real `.docx` ZIP package ingestion;
- paragraph extraction;
- table-cell signal extraction;
- safe metadata;
- honest rejection of malformed input;
- no network or fake OCR claim.

## PDF contract

The PDF product test verifies:

- PDF text-layer extraction;
- summary generation;
- safe metadata;
- honest image-only PDF failure until OCR exists;
- no cloud OCR claim.

## XLSX/Excel contract

KR-2F introduces a portable stdlib XLSX OOXML inspector as the first XLSX product contract. It verifies:

- workbook package opens;
- workbook sheet metadata is readable;
- worksheet XML exists;
- non-empty cells are counted;
- table-like rows are detected;
- formulas are inventoried;
- malformed workbooks fail honestly;
- no destructive edit is performed.

This is intentionally not full Excel parity and not a replacement for a future XLSX service.

## Non-goals

KR-2F does not:

- implement a full spreadsheet engine;
- evaluate formulas;
- render charts;
- edit XLSX files;
- move or delete `docs/codex`;
- retire RF3 legacy tests;
- claim Kimi-level or selected workflow parity.

## Acceptance criteria

```text
targeted KR-2F checks pass;
DOCX/PDF/XLSX product workflow report is ready;
post-audit is generated;
post-test-map is generated;
post-stage-dependency inventory is generated;
product aliases remain ready;
low-risk operator/static replacements remain ready;
Slides product quality replacements remain ready;
product docs remain ready;
stage docs deprecation remains ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
