# KR-2E Slides Product Quality Replacement Tests

KR-2E adds product-named tests for the accepted KQ-1A/B/C Slides quality behavior.

## Purpose

The previous KQ phase proved important capabilities:

- deck artifact bundle quality harness;
- actual PPTX generation for an executive memo deck;
- independent PPTX render and visual QA loop;
- conservative claim boundaries around Kimi-level, selected parity, Server 3 proof, and human approval.

Those capabilities are valuable product behavior, but their test names are still tied to historical KQ stage labels. KR-2E starts the replacement by adding product-level tests.

## Added product tests

```text
backend/tests/quality/test_artifact_bundle_quality_product_contract.py
backend/tests/workflows/test_slides_exec_memo_generation_product_contract.py
backend/tests/quality/test_pptx_render_qa_product_contract.py
backend/tests/smoke/test_slides_product_quality_replacements.py
```

## Added checker

```text
scripts/kw_slides_product_quality_replacements_check.py
```

## Legacy safety net

KR-2E does not remove legacy KQ tests/checkers. They stay until product-level tests provide enough replacement coverage across full runner and Docker smoke.

## Portable render behavior

General full-runner checks must remain portable across machines. If a machine lacks LibreOffice/pdftoppm and python-pptx/Pillow, product render tests may skip real render execution. Real independent render evidence is still required in targeted runs on a machine with a render stack.

## Non-goals

KR-2E does not:

- move or delete `docs/codex`;
- remove legacy KQ tests;
- add source-grounded Slides generation;
- claim Kimi-level quality;
- prove selected workflow parity;
- verify Server 3 local intranet GigaChat route.

## Acceptance criteria

```text
targeted KR-2E checks pass;
Slides product quality replacement report is ready;
post-audit is generated;
post-test-map is generated;
post-stage-dependency inventory is generated;
product aliases remain ready;
low-risk operator/static replacements remain ready;
product docs remain ready;
stage docs deprecation remains ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
