# KR-2B Product Test Aliases

KR-2B introduces product-level test suites without deleting legacy stage tests.
The goal is to start moving the repository from patch-history validation toward
stable product contracts while preserving the current safety net.

## Product test roots

The canonical product test layout is:

```text
backend/tests/workflows/
backend/tests/quality/
backend/tests/integrations/
backend/tests/operators/
```

These suites are not allowed to depend on a machine-specific checkout path,
profile label, downloads directory, branch name, or commit SHA. They must test
portable product behavior.

## Alias strategy

Legacy stage tests and checker scripts remain in place until replacement
coverage is accepted. KR-2B adds product tests that alias existing accepted
capabilities:

| Product area | Product test file | Current bridge |
| --- | --- | --- |
| DOCX/PDF workflows | `backend/tests/workflows/test_product_workflow_aliases.py` | `scripts/kw_docx_pdf_real_ingestion_check.py` |
| XLSX workflow | `backend/tests/workflows/test_product_workflow_aliases.py` | canonical XLSX docs; runtime planned for KR-5 |
| Slides quality | `backend/tests/quality/test_product_quality_aliases.py` | KQ-1A/KQ-1B/KQ-1C checker scripts |
| Operator readiness | `backend/tests/operators/test_product_operator_aliases.py` | full runner, readiness gate, Docker smoke tooling |
| Path portability | `backend/tests/integrations/test_product_path_portability_contract.py` | new product alias files must be path-neutral |

This is intentionally a bridge, not a claim that all stage tests are obsolete.

## XLSX status

XLSX/Excel is mandatory product scope. KR-2B does not implement the XLSX runtime;
it locks in the product-test target and prevents XLSX from being treated as an
optional future note. The runtime belongs to the KR-5 sequence.

## Physical archive rule

`docs/codex` remains in place until legacy checker scripts and tests stop reading
it directly. Physical archival of stage documentation is blocked until KR-2B/KR-2C
replacement coverage proves that product-level tests have taken over the relevant
contracts.

## Acceptance criteria

KR-2B is ready when:

- product workflow, quality, integration, and operator test roots exist;
- product-level alias tests pass;
- new alias files are path-neutral;
- canonical product docs remain ready;
- stage documentation deprecation check remains ready;
- production readiness gate still passes.
