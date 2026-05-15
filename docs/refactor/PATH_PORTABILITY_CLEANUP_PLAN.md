# KR-3B Path Portability Cleanup Plan

KR-3B converts KR-3A warn-only portability findings into a controlled cleanup plan.

## Purpose

KR-3A established the enforcement boundary:

```text
protected product surface -> blocking
legacy/stage surface      -> warn-only
```

KR-3B does not fix all warn-only findings. It classifies them so later KR patches can handle them safely.

## Cleanup batches

### Legacy stage baseline pin retirement

Stage scripts may contain raw commit SHAs and release branch names from old checkpoint workflows. These should not be active product portability requirements.

Action:

```text
archive_or_reclassify_stage_checkers_after_product_replacements
```

This should happen only after product replacement checks cover the behavior.

### Local examples rewrite or mark

Historical runbooks or refactor notes may contain `/home/...`, profile labels, or localized Downloads examples.

Action:

```text
rewrite as placeholders or mark as explicit local-only example
```

Preferred replacements:

```text
<repo-root>
<downloads-dir>
$REPO_DIR
$DOWNLOADS_DIR
```

### docs/codex dependency retirement

`docs/codex` still has direct dependencies from stage checkers/tests. Physical archive is blocked until those dependencies are removed or archived.

Action:

```text
defer_until_stage_checker_dependency_inventory_is_cleared
```

### Legacy smoke test replacement/archive

Legacy smoke tests may encode old stage assumptions. They should be replaced with product tests or archived after product coverage exists.

### Operator script portability review

Operator scripts should use arguments such as `--repo-root`, `--output-dir`, environment variables, or relative paths instead of fixed branch/commit/machine assumptions.

## Non-goals

KR-3B does not:

- rewrite legacy files;
- remove tests;
- move `docs/codex`;
- change production runtime behavior;
- claim that portability debt is fixed.

## Acceptance criteria

```text
KR-3B cleanup plan reports ready;
legacy warn-only findings are classified into cleanup batches;
physical docs/codex archive remains blocked;
KR-3A path portability policy remains ready;
post-audit is generated;
post-test-map is generated;
post-stage-dependency inventory is generated;
product replacement checks remain ready;
production readiness gate checks-only passes;
full runner passes after commit;
Docker smoke passes on the same committed HEAD.
```
