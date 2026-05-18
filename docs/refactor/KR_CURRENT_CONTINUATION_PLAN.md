# KR Current Continuation Plan

This document records the current continuation point for Knowledge_Work_Studio / KW Studio after inspecting the full Git data package.

It supersedes older migration anchors that stopped at KR-2A or treated KR-2B as the next unresolved patch.

## Current factual checkpoint

```text
branch: 9_Product_Release_Hardening
HEAD: 3a174aec572b571cb56343ddfb8095643b892c3e
origin/9_Product_Release_Hardening: 3a174aec572b571cb56343ddfb8095643b892c3e
checkpoint status: KR-3C accepted
working tree expectation: clean before the next patch
```

The uploaded full Git package contains branch refs and a restored working tree. The restored tree may initially open on `main`; operators must explicitly check out `origin/9_Product_Release_Hardening` before continuing KR work.

## Decision

Continue from the accepted KR-3C checkpoint, not from the stale KR-2A / KR-2B recovery point.

The intended cleanup direction is:

```text
remove unnecessary historical documentation safely;
replace stage-specific tests with product-level tests;
stop making active tests depend on specific historical commits or branch baselines;
remove profile/path/commit-specific assumptions from the protected product surface;
only archive docs/codex after direct dependencies are removed or archived.
```

## Why the plan changed

Earlier migration notes described KR-2B as started but not accepted. The full Git history shows that KR-2B through KR-3C were subsequently committed and accepted.

The correct interpretation is not that cleanup was abandoned. The cleanup was made safer and more incremental:

1. inventory the legacy documentation, tests, scripts, and portability debt;
2. add product-level replacement tests and checkers;
3. classify legacy references into cleanup batches;
4. record legacy baseline-pin retirement manifests;
5. only then remove or archive legacy files in controlled follow-up patches.

## What has already been done

The KR work after KR-2A added product replacement coverage and cleanup planning without deleting legacy assets.

Observed repository snapshot at the current checkpoint:

```text
tracked files: 847
Markdown files: 192
docs Markdown files: 166
docs/codex Markdown files: 103
backend test files: 219
scripts: 143
commits on origin/9_Product_Release_Hardening: 473
commits after KR-2A checkpoint 2423ed4: 18
```

Change shape after KR-2A:

```text
46 changed files
42 added files
4 modified files
0 deleted files
4452 insertions
```

This is intentional. It means the project added product-facing replacement structure before performing destructive cleanup.

## Useful full-project data

### Highest-trust continuation data

Use the Git data as the source of truth for continuation state:

```text
.git/HEAD
refs/remotes/origin/9_Product_Release_Hardening
packed refs
commit history
bundle refs
working tree status after checkout
```

The current branch HEAD is more reliable than older external migration notes.

### Product source tree

The current source tree is needed for real patches and validation:

```text
backend/
frontend/
scripts/
docs/product/
docs/architecture/
docs/workflows/
docs/quality/
docs/operators/
docs/refactor/
```

Patches should be built from the actual checked-out tree, then verified with `git diff`, `git apply --check`, syntax checks, and targeted tests whenever feasible.

### Refactor documentation and machine-readable checkers

The following files are especially useful because they encode the cleanup policy and current dependency map:

```text
docs/refactor/REPOSITORY_CLEANUP_AUDIT.md
docs/refactor/REPOSITORY_CLEANUP_POLICY.md
docs/refactor/STAGE_DOCUMENTATION_DEPRECATION_INDEX.md
docs/refactor/TEST_INVENTORY_PRODUCT_MAP.md
docs/refactor/STAGE_CHECKER_DEPENDENCY_INVENTORY.md
docs/refactor/PATH_PORTABILITY_POLICY.md
docs/refactor/PATH_PORTABILITY_CLEANUP_PLAN.md
docs/refactor/LEGACY_STAGE_BASELINE_PIN_RETIREMENT_BATCH1.md
```

Useful checkers:

```text
scripts/kw_product_test_aliases_check.py
scripts/kw_stage_checker_dependency_inventory.py
scripts/kw_docx_pdf_xlsx_product_workflows_check.py
scripts/kw_slides_product_quality_replacements_check.py
scripts/kw_path_portability_policy_check.py
scripts/kw_path_portability_cleanup_plan.py
scripts/kw_legacy_stage_baseline_pin_retirement.py
scripts/kw_production_readiness_gate.py
```

### Legacy documentation

`docs/codex` is useful as development history and as a dependency source for legacy stage checkers.

It is not the product documentation source of truth, and new product documentation must not be added there.

Physical movement or deletion remains blocked until the direct `docs/codex` dependencies are removed or archived.

### Root historical prompt packs and old runbooks

Root-level phase prompt packs and older runbooks are useful for forensic reconstruction, but they are cleanup candidates. They should eventually be moved to an archive or replaced by product-facing operator docs after active references are checked.

Examples:

```text
*_PHASE_ISSUE_PACK.md
*_ANTI_SCOPE_PROMPTS_REVISED.md
*_REVIEW_TACTICS.md
CODEX_RUNBOOK.md
LEGACY_MIGRATION_RUNBOOK.md
MIGRATION_PROMPT_PACK.md
```

### Stashes and local-only data

Stashes or machine-local remotes can explain prior failed hotfix attempts. They should not be applied blindly.

Local paths such as `/home/...`, localized Downloads paths, profile labels, branch names, and raw commit SHAs are evidence for cleanup, not requirements for new product tests.

## Done vs. remaining cleanup intent

| Intent | Already done | Remaining work |
| --- | --- | --- |
| Remove unnecessary documentation | Canonical product docs exist; `docs/codex` is deprecated; dependency inventory exists | Remove/archive only after active dependencies are cleared |
| Make tests product-level | Product workflow, quality, operator, and integration tests were added | Keep replacing or retiring legacy stage smoke/checker coverage |
| Remove commit-specific test assumptions | Portability scanner and baseline-pin retirement manifest exist | Remove active gate references to legacy baseline-pinned stage scripts |
| Remove local path/profile assumptions | Protected product surface is checked separately | Rewrite or mark local examples; then clean legacy warning scope |
| Preserve safety | No destructive cleanup yet; legacy safety net remains | Reduce safety-net dependence in small verified batches |

## Next continuation plan

### KR-3D — Product entrypoint and local-example cleanup

Purpose:

```text
rewrite unmarked local examples as placeholders;
mark truly local examples as local-only;
make README and active docs point to product documentation first;
do not move docs/codex;
do not delete legacy scripts or tests.
```

Acceptance:

```text
path portability policy remains ready;
path portability cleanup plan remains ready;
legacy baseline-pin retirement report remains ready;
product replacement checks remain ready;
production readiness gate checks-only passes;
full runner and Docker smoke must pass before CLOSED / ACCEPTED.
```

### KR-3E — Active gate reference retirement

Purpose:

```text
remove active production-readiness-gate dependence on legacy stage baseline-pinned scripts only after product replacements cover the behavior;
keep or archive retired checkers explicitly;
do not weaken product gates.
```

### KR-3F — Controlled archive/delete batch

Purpose:

```text
archive inactive legacy docs/checkers that are no longer referenced;
keep machine-readable inventory of every archived/deleted path;
verify no docs/codex direct dependencies remain for moved files.
```

### KR-4A and later

After cleanup pressure is reduced, continue product development:

```text
KR-4A: workflow contract core;
KR-5A: XLSX inspect workflow;
KR-5B: XLSX validation and artifact bundle;
KR-6A: source-grounded slides continuation.
```

## Rules for the next patch

```text
inspect actual git status first;
continue from 3a174ae unless a newer branch head is present;
do not use stale KR-2A/KR-2B instructions as the active checkpoint;
do not physically move docs/codex until direct dependencies are cleared;
do not delete legacy tests before product replacements prove coverage;
do not make active product tests depend on raw commit SHAs;
do not claim Kimi-level quality or Server 3 proof without evidence;
do not run npm audit fix --force without a controlled dependency/security patch.
```
