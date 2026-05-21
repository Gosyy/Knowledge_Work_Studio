# KR-2A Test Inventory and Product Test Map

KR-2A is a planning and inventory stage. It does not delete, move, or rename any tests.

The goal is to turn the repository's accumulated stage-specific smoke tests into a controlled product-test migration plan. Earlier phases proved many capabilities through files named after implementation stages such as `S13`, `P10`, `RF`, `RC`, and `KQ`. Those tests are useful historical evidence, but they should not remain the long-term shape of the product test suite.

## Why this stage exists

KR-1B showed that physically moving `docs/codex` too early breaks legacy checker scripts and smoke tests. KR-1B-R2 therefore marked stage documentation as deprecated while leaving it in place. KR-2A continues that safe approach: first map test and checker dependencies, then rewrite or retire them in later patches.

## Product test target structure

The long-term test suite should be organized by product behavior instead of patch history:

```text
backend/tests/api/
backend/tests/workflows/
backend/tests/quality/
backend/tests/integrations/
backend/tests/operators/
```

Mandatory workflow coverage:

- DOCX workflow
- PDF workflow
- XLSX / Excel workflow
- Slides workflow
- Python analysis workflow
- Browser evidence workflow

Mandatory quality coverage:

- artifact bundle contract
- provenance manifest
- PPTX independent render QA
- XLSX validation
- source grounding

## What the KR-2A tool produces

`scripts/kw_test_inventory_product_map.py` reads a KR-0A audit ZIP or scans the repository directly. It writes:

```text
kr2a_test_inventory_product_map.json
kr2a_test_inventory_product_map.md
kr2a_test_decisions.json
kr2a_script_decisions.json
kr2a_product_test_targets.json
kr2a_physical_archive_blockers.json
```

The key output is `physical_archive_blockers`: tests and checker scripts that still depend on stage documentation or stage-specific names. These must be rewritten or retired before `docs/codex` can be physically archived.

## What KR-2A does not do

KR-2A does not:

- delete tests;
- rename tests;
- move `docs/codex`;
- weaken production readiness;
- claim the stage cleanup is complete.

## Next stages

- KR-2B: create/rename product workflow and quality tests.
- KR-2C: retire or archive replaced stage-specific smoke tests and checker scripts.
- KR-3A/KR-3B: neutralize hardcoded path/profile/branch/commit assumptions.
- Later: physically archive `docs/codex` after checker dependencies are gone.
