# Test portfolio rationalization plan

## Purpose

The project currently has many tests because it accumulated safety nets during product reset, cross-profile hardening, runtime topology hardening, Slides KR phases, artifact bundle checks and deployment fixes. Before implementing the large KR-7 Slides roadmap, the test portfolio must be audited and rationalized.

The goal is not to delete tests aggressively. The goal is to reduce duplicate maintenance cost while preserving product confidence.

## Current concern

The operator is concerned that the test suite is too large and may contain redundant, overlapping or obsolete checks. This concern is valid. A large suite is useful only when tests are organized by purpose and failure meaning is clear.

## Principles

Do not delete tests because they are inconvenient.

Do delete, merge, quarantine or downgrade tests when:

- they duplicate another stronger contract;
- they assert stale stage-history assumptions;
- they test implementation details that are no longer product contracts;
- they are brittle across profiles;
- they slow full runner without adding unique risk coverage;
- they hide product failures by over-mocking;
- they belong to historical scaffolding no longer used by active gates.

Preserve tests when they protect:

- public API contracts;
- artifact bundle contracts;
- provenance/citation contracts;
- production/offline runtime guardrails;
- security/secrets behavior;
- Postgres/Docker deploy behavior;
- source-mode routing;
- render/visual QA;
- migration/handoff documentation policy;
- acceptance runner behavior.

## Proposed test tiers

### Tier 0 — static and hygiene checks

Runs fast on every patch.

Examples:

- `py_compile` changed Python files;
- `git diff --check`;
- documentation wording/unsupported-claims scanner;
- project handoff checker;
- config schema smoke.

Policy: keep fast and strict.

### Tier 1 — contract unit tests

Runs targeted by module.

Examples:

- PresentationIR schema validation;
- GigaChat runtime mode validation;
- source asset extraction units;
- chart data validator;
- visual block validator;
- API schema normalization.

Policy: keep; consolidate duplicates.

### Tier 2 — workflow tests

Runs on affected workflows.

Examples:

- DOCX workflow bundle;
- XLSX inspect workflow;
- Slides source-grounded workflow;
- Slides render/visual QA bundle;
- KR-6D planning parser/repair;
- future KR-7 PresentationIR workflow.

Policy: keep one strong workflow contract per feature; merge overlapping micro-regressions.

### Tier 3 — API integration tests

Runs core API paths without Docker.

Examples:

- session/task/artifact API;
- slides generation API;
- source upload/binding API;
- presentation API future endpoints.

Policy: keep stable public API tests; remove tests that duplicate service internals.

### Tier 4 — smoke/gate scripts

Runs readiness and project gates.

Examples:

- RF/S/K production readiness gates;
- Docker compose config check;
- render stack check;
- public GigaChat mode check;
- migration handoff check.

Policy: keep gates but reduce branch-history/stage-history brittleness.

### Tier 5 — full runner

Project-wide acceptance runner.

Policy: keep as final local acceptance. It may call curated subsets rather than every historical test if rationalization creates a clean test index.

### Tier 6 — Docker smoke

Production-like container startup and health/readiness smoke.

Policy: mandatory before local accept.

### Tier 7 — real public GigaChat evidence tests

Manual/operator-triggered only, secret-safe, never default CI.

Policy: keep as evidence runner for LLM quality phases.

## Audit method

Create an inventory script before deleting anything:

```text
scripts/kw_test_inventory.py
```

Output:

```json
{
  "tests": [
    {
      "path": "backend/tests/...",
      "tier": "workflow|api|smoke|quality|unit|legacy",
      "runtime_cost": "fast|medium|slow|docker|external",
      "contract": "slides_source_mode_routing",
      "overlaps_with": [],
      "decision": "keep|merge|quarantine|delete|rewrite",
      "reason": "..."
    }
  ]
}
```

## Decision categories

### Keep

The test protects a live contract and has clear failure meaning.

### Merge

Multiple tests protect the same behavior. Keep the strongest scenario and merge important assertions.

### Quarantine

The test protects a historical or unstable contract. It should not block product full runner until rewritten.

### Delete

The test protects no active contract, is fully superseded, and deletion is documented.

### Rewrite

The contract is valid, but the test is brittle, too implementation-specific or too slow.

## Tests likely worth preserving

- API contract tests for sessions/tasks/artifacts;
- production readiness gates;
- GigaChat runtime mode guardrails;
- Postgres metadata truth checks;
- Docker smoke;
- source-mode routing tests;
- artifact manifest and quality report tests;
- render/visual QA tests;
- public GigaChat test mode tests;
- migration handoff checker;
- frontend build/e2e smoke.

## Tests likely worth reviewing for consolidation

- repeated Slides placeholder leakage tests across workflow/API/smoke layers;
- old stage-history lineage checks;
- duplicate RF/R/S smoke variants that assert the same readiness marker;
- tests that only assert file existence where stronger manifest tests already verify hash/size/content;
- low-level implementation tests for legacy outline builder after PresentationIR becomes canonical;
- frontend tests that duplicate Playwright smoke but do not protect user-visible behavior;
- multiple parser tests that can be table-driven in one file.

## Safe rationalization sequence

1. Add inventory tooling.
2. Generate test inventory report.
3. Classify every test by contract/tier/cost.
4. Identify duplicate clusters.
5. Propose deletion/merge list in documentation before changing tests.
6. Apply one small rationalization patch at a time.
7. Run targeted tests for the affected cluster.
8. Run full runner and Docker smoke.
9. Update handoff.

## What not to do

Do not delete tests before a contract map exists.

Do not remove production guardrail tests to reduce runtime.

Do not remove Docker smoke.

Do not remove public API tests while replacing the frontend.

Do not remove source-mode routing tests before PresentationIR compatibility is proven.

Do not remove legacy tests simply because a new implementation exists; first prove the legacy behavior is no longer required or is covered by a stronger contract.

## Suggested first test-audit patch

Create:

```text
scripts/kw_test_inventory.py
backend/tests/test_portfolio/test_inventory_classification.py
```

Generate:

```text
logs/test_inventory_*.json
logs/test_inventory_*.md
```

Do not delete any test in that first patch. The first patch only makes the test portfolio visible.

<!-- KR7A1_INVENTORY_IMPLEMENTATION_CONTRACT -->

## KR-7A.1 inventory implementation contract

The first inventory implementation must be strong enough to support later rationalization decisions. It must not be a brittle keyword-only classifier.

Required behavior:

- path-first classification before keyword classification;
- directory-aware handling for newly created test directories and dirty trees;
- primary `contract` plus full `contracts` membership for cross-cutting tests;
- deterministic tiers and runtime-cost labels;
- no `delete` decision in the first inventory patch;
- mandatory preservation of acceptance runners, Docker smoke, production readiness, GigaChat runtime, source-mode routing, render/visual QA and Slides workflow contracts;
- JSON and Markdown reports that can be archived as evidence;
- tests that prove Slides workflow files are not swallowed by incidental `gigachat`, `artifact`, `runtime`, or `source` keywords.

Known failure mode discovered during KR-7A.1: the initial classifier evaluated keyword rules before path ownership, so no primary `slides_workflow` classification was produced. Repair must fix taxonomy design, not only add one brittle special case.

<!-- KR7_VENV_ONLY_DEV_RULE -->

## Test inventory execution environment

All test inventory scripts and test-portfolio checks must run through the project `.venv`.

Inventory runners must prefer `<project-root>/.venv/bin/python`, verify `pytest` and required project dependencies, and fail clearly if the environment is missing. Running `scripts/kw_test_inventory.py` or its pytest coverage through system Python is not accepted evidence when `.venv` exists.


<!-- KR7A1_PYTEST_COLLECTION_SCOPE -->

## Pytest collection scope guardrail

Test inventory and recovery runners may archive evidence under `logs/`. Those reports can contain snapshots of test files. The test portfolio must never allow pytest to collect evidence snapshots as live tests.

Policy:

```text
pytest test discovery is scoped through `pytest.ini`;
project-wide backend tests target `backend/tests`;
logs, storage, frontend build outputs, `.venv`, `.pytest_cache`, `node_modules`, Playwright reports and other runtime artifacts are excluded from collection;
inventory reports classify tests but do not become test sources.
```

This guardrail is part of KR-7A.1 because test rationalization produces additional reports and must not destabilize full runner collection.
