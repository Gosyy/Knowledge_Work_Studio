# Definition of Done

## Purpose

This document defines when a KW Studio patch may be considered complete. It applies to code, tests, docs, runners, deploy scripts, workflow contracts, and cleanup patches.

## Patch-level DONE

A patch is DONE only when all applicable items are true:

```text
actual local full-history checkout was verified;
actual branch/HEAD/dirty tree were recorded;
the exact patch or repair package was applied and tested on that verified local checkout before it was sent to the operator;
related docs, source files, tests, runners, and contracts were audited;
problem is solved directly, not bypassed;
no hidden workaround or unsupported product claim was introduced;
no production/offline guardrail was weakened;
no fallback is presented as normal success;
profile neutrality is preserved;
PROJECT_MIGRATION_HANDOFF.md is updated when required;
quality/prohibition/governance docs are updated when required;
changed Python files pass syntax/import checks;
changed shell scripts pass bash -n;
git diff --check passes;
targeted tests/checkers pass;
logs are produced, archived, and reviewed when runners are executed;
working tree state is known and clean or explicitly explained.
```

## Acceptance labels

Use these labels consistently:

```text
TARGETED PASS        apply/repair runner and targeted checks passed
LOCAL ACCEPT         targeted checks + full runner + Docker smoke passed on committed HEAD
REMOTE ACCEPT/CLOSED commit pushed and remote verified
FAIL                 real product/test/syntax/validation/runtime failure
RUNNER BUG           helper/runner behavior failed independently of product logic
PARTIAL              useful progress exists, but acceptance is incomplete
```

## Local acceptance

`LOCAL ACCEPT` requires:

```text
patch committed locally;
project-resident full runner passes on committed HEAD;
project-resident Docker smoke passes on the same committed HEAD;
logs are archived and reviewed;
tracked working tree is clean or only known generated files were restored/acknowledged.
```

Project-resident entrypoints:

```bash
bash scripts/kw_product_full_runner_logged.sh
bash scripts/kw_product_docker_smoke_logged.sh --backend-port 18000 --frontend-port 13000
```

## Remote acceptance

`REMOTE ACCEPT / CLOSED` requires:

```text
commit pushed to origin/9_Product_Release_Hardening;
remote commit verified;
no unexpected divergence from the operator's active branch;
acceptance logs reviewed after push if the operator reruns validation.
```

## Product behavior rule

Tests passing is necessary but not sufficient. A workflow is acceptable only if the user-facing product behavior satisfies the relevant workflow contract.

Examples:

```text
Slides: generated public PPTX text must not leak prompt echo, template labels, placeholders, or internal technical labels.
Template rewrite: all non-locked text blocks must be rewritten and source text must not leak.
XLSX: artifact manifests, formula inventory, source evidence, and quality reports must be consistent and fail closed.
Deploy: Postgres credential drift must not be hidden by container-only cleanup.
```

## Documentation DONE

Documentation changes are DONE only when:

```text
the authoritative document was updated;
PROJECT_MIGRATION_HANDOFF.md contains only a durable summary and links;
AGENTS.md and CODEX_PROJECT_BRIEFING.md remain short entrypoints;
QUALITY_MATRIX.md reflects any workflow maturity/status change;
PROJECT_PROHIBITIONS.md reflects any new forbidden shortcut;
ADR exists for cross-cutting architecture or governance decisions;
spelling, stale claims, unsupported claims, and profile-specific wording were checked;
scripts/kw_assistant_governance_check.py --require-ready passes.
```
