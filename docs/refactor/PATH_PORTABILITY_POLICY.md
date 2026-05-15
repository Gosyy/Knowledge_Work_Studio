# KR-3A Path Portability Policy

KR-3A hardens path portability scanning before the broader KR-3B cleanup.

## Purpose

KW Studio must work outside a specific user profile, machine, checkout path, branch name, or commit hash. Product code and tests must not depend on machine-local examples such as local home directories or localized Downloads folders.

KR-3A adds an enforceable scanner for the protected product surface. It does not attempt to fix every historical finding in one patch.

## Protected product surface

The protected surface includes:

```text
docs/product/
docs/architecture/
docs/workflows/
docs/quality/
docs/operators/
backend/tests/workflows/
backend/tests/quality/
backend/tests/operators/
backend/tests/integrations/
product/workflow/quality replacement scripts
```

The scanner blocks unmarked occurrences of:

```text
absolute home paths
profile labels
localized Downloads folders
release branch names
raw 40-character git SHAs
```

## Local operator examples

Operator runbooks may contain local path examples only when they are explicitly marked as local-only examples. The goal is to keep examples useful without turning them into product requirements.

Accepted wording examples:

```text
Local-only example:
machine-local example:
operator local example:
local path example:
```

## Marker catalogs

Some scanner tests and checker scripts intentionally contain forbidden marker strings so they can verify detection behavior. Those files are explicit marker catalogs and are allowlisted.

## Legacy debt

KR-3A reports legacy/stage findings as warn-only. KR-3B is responsible for fixing or reclassifying those findings in controlled patches.

## Non-goals

KR-3A does not:

- rewrite all existing path references;
- delete legacy stage tests;
- move `docs/codex`;
- change runtime behavior;
- change deployment topology.

## Acceptance criteria

```text
KR-3A scanner reports ready;
protected product surface has zero blocking findings;
local-only operator examples are allowed only when marked;
raw commit hashes and branch pins are detected in product tests/docs;
post-audit is generated;
post-test-map is generated;
post-stage-dependency inventory is generated;
product replacement checks remain ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
