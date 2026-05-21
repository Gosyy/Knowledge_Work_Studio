# KR-2D Low-Risk Operator/Static Replacement Tests

KR-2D is the first small replacement step after the KR-2C dependency inventory.

## Purpose

The goal is to start replacing stage-specific smoke coverage with product-level tests in low-risk areas.

KR-2D does **not** delete or move legacy tests. It adds product-level tests first, while legacy stage tests remain as a safety net.

## Why this step exists

KR-2C showed that many stage checker scripts and tests still read `docs/codex/*.md` directly. Therefore `docs/codex` cannot be physically archived yet.

Before deleting or moving historical files, KW Studio needs product-level replacement coverage for stable, low-risk behavior:

- operator log archive behavior;
- canonical product documentation readiness;
- repository cleanup audit output contracts;
- stage checker dependency inventory output contracts.

## Added product-level coverage

KR-2D adds product-oriented tests under `backend/tests/operators/`:

```text
backend/tests/operators/test_log_archive_product_contract.py
backend/tests/operators/test_product_docs_operator_contract.py
backend/tests/operators/test_cleanup_audit_operator_contract.py
backend/tests/operators/test_stage_dependency_inventory_operator_contract.py
```

It also adds a smoke-level readiness check:

```text
backend/tests/smoke/test_low_risk_operator_static_replacements.py
```

and a report/check script:

```text
scripts/kw_low_risk_operator_static_replacements_check.py
```

## What this replaces conceptually

KR-2D starts replacement coverage for low-risk historical areas such as:

```text
backend/tests/smoke/test_operator_logging_downloads_policy.py
scripts/kw_operator_logging_policy_check.py
backend/tests/smoke/test_repository_cleanup_audit.py
backend/tests/smoke/test_stage_checker_dependency_inventory.py
```

Those files are not removed in KR-2D. They remain until later KR cleanup stages prove enough replacement coverage and update production gates safely.

## Non-goals

KR-2D does not:

- move `docs/codex`;
- delete legacy stage tests;
- rewrite live GigaChat checks;
- rewrite selected benchmark or human review packet flows;
- claim Kimi-level quality;
- add new runtime product workflows.

## Acceptance criteria

KR-2D is acceptable only when:

```text
targeted KR-2D checks pass;
product docs remain ready;
stage docs deprecation remains ready;
stage checker dependency inventory remains ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
