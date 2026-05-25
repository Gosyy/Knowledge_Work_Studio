# Assistant Operating Rules

## Purpose

This document is the short operating contract for any assistant or coding agent working on KW Studio. It consolidates rules that are explained in detail across `AGENTS.md`, `docs/refactor/CODEX_PROJECT_BRIEFING.md`, `docs/refactor/PROJECT_MIGRATION_HANDOFF.md`, the KR roadmap, workflow docs, and quality docs.

Do not treat this file as a replacement for the detailed documents. Treat it as the first checklist that points to the rest of the project governance layer.

## Mandatory reading before any change

Before code, tests, docs, runners, deploy scripts, or cleanup changes, read:

```text
README.md
AGENTS.md
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
docs/refactor/CODEX_PROJECT_BRIEFING.md
docs/refactor/KR_PRODUCT_RESET_ROADMAP.md
docs/architecture/WORKFLOW_CONTRACT_CORE.md
```

For workflow-specific work, also read the relevant workflow, quality, operator, roadmap, and test-rationalization documents.

## Mandatory local preflight

Do not issue a code patch, repair runner, test rewrite, test deletion, or migration script unless an actual local full-history checkout has been verified.

Record at minimum:

```bash
git rev-parse --is-shallow-repository
git status --short --branch
git rev-parse HEAD
git rev-parse origin/9_Product_Release_Hardening || true
git log --oneline --decorate --graph -20
git branch -vv
git remote -v
```

Expected:

```text
git rev-parse --is-shallow-repository -> false
```

If a current local full-history checkout is not available, stop and ask the operator for a full-history clone or mirror archive. GitHub file browsing and uploaded logs are useful evidence, but they are not a substitute for local patch validation.

## Mandatory `.venv` rule

All project analysis and validation must use the project `.venv` when it exists. If it does not exist, create it before validation:

```bash
test -d .venv || python3 -m venv .venv
. .venv/bin/activate
python -c "import sys; print(sys.executable)"
python -m pip --version
python -m pytest --version
```

The Python executable used for tests and project scripts must resolve inside `<project-root>/.venv` unless a specific bootstrap phase is explicitly creating that environment.

## Mandatory pre-patch report

Before changing files, produce or internally complete the pre-patch report defined in:

```text
docs/templates/PRE_PATCH_REPORT_TEMPLATE.md
```

The report must include:

```text
task;
current local repository state;
remote/branch/HEAD status;
dirty tree classification;
docs inspected;
related code/tests/runners inspected;
contracts affected;
risk map;
patch plan;
validation plan;
expected ACCEPT criteria.
```

## Implementation rules

- Work at senior engineer level.
- Solve the real issue; do not bypass it.
- Prefer small, complete, reversible patches over broad risky rewrites.
- Do not use brittle text anchors unless the script first proves the exact expected pre-state and exits before modifying anything on mismatch.
- Do not weaken production/offline guardrails to make tests pass.
- Do not hide product failures behind fallback text, fake metadata, fake charts, generated images, or misleading success states.
- Do not patch tests to hide real product failures.
- Keep product code, tests, Dockerfiles, and reusable docs profile-neutral.
- Keep logs secret-safe.
- Update documentation when behavior, contracts, acceptance criteria, workflow status, runtime modes, runner behavior, or operating procedures change.

## Documentation stewardship rules

The assistant must maintain project documentation as a structured governance system, not as an append-only chat transcript.

When a patch changes a rule, phase, workflow contract, runner, acceptance criterion, runtime mode, profile behavior, or known failure mode:

1. Update the closest authoritative document, not only the handoff.
2. Update `docs/refactor/PROJECT_MIGRATION_HANDOFF.md` with a short durable summary and links.
3. Update `docs/QUALITY_MATRIX.md` when workflow maturity, validation, provenance, QA, or status changes.
4. Update `docs/PROJECT_PROHIBITIONS.md` when a new forbidden shortcut or failure mode is discovered.
5. Add or update an ADR under `docs/adr/` when the change is architectural, cross-cutting, or changes decision policy.
6. Keep `AGENTS.md` and `docs/refactor/CODEX_PROJECT_BRIEFING.md` as short entrypoints; do not paste long duplicated policy blocks into them.
7. If a handoff section becomes stale, mark it historical or replace it with a current-state pointer instead of leaving contradictory “current phase” text.
8. Do not introduce unsupported claims, stale commit assumptions, profile-specific wording, or spelling drift in docs, CLI help, comments, or user-facing messages.

Documentation updates must be checked by `scripts/kw_assistant_governance_check.py` before a patch is considered ready.

## Mandatory post-patch report

After changes, produce or internally complete the post-patch report defined in:

```text
docs/templates/POST_PATCH_REPORT_TEMPLATE.md
```

The report must explain:

```text
files changed;
why the change is not a workaround;
product behavior changed;
docs updated;
tests/checkers run;
log artifacts produced;
known limitations;
ACCEPT / REJECT / PARTIAL recommendation.
```

## Log analysis rule

When the operator uploads logs, analyze them with the structure in:

```text
docs/templates/LOG_ANALYSIS_TEMPLATE.md
```

Do not declare ACCEPT from impressions. Use evidence from logs and classify the result as:

```text
ACCEPT
REJECT
PARTIAL
RUNNER BUG
ENVIRONMENT ISSUE
```

## Acceptance rule

A patch is not accepted until the project Definition of Done is satisfied. See:

```text
docs/DEFINITION_OF_DONE.md
```
