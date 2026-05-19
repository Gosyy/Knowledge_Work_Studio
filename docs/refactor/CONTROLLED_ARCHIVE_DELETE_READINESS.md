# KR-3F Controlled Archive/Delete Readiness

KR-3F starts the first physical cleanup batch after KR-3E removed active
production-readiness-gate references to the first legacy baseline-pinned stage
checker group.

This patch is intentionally conservative: it archives a small group of
root-level historical prompt packs that are not active product
contracts. It does not move `docs/codex`, does not delete stage checkers, and
does not weaken production quality gates.

## Product reason

KW Studio is moving from a stage-history repository toward an offline/intranet,
artifact-first, provenance-first, operator-gated knowledge-work product. Root
prompt packs from older development phases are useful as forensic history, but
keeping them at repository root makes them look like active operator entrypoints.

KR-3F moves the first low-risk group under:

```text
docs/archive/development-history/root-prompt-packs/
```

## Batch 1 policy

A file is eligible for this first batch only when all of the following are true:

```text
it is root-level historical Markdown, not product source code;
it is not README.md or AGENTS.md;
it is not under docs/codex;
it is not required by production readiness gate;
it is not referenced by active code, tests, scripts, or product docs at its old root path;
it remains available in the archive for audit/restore.
```

## Batch 1 moved paths

```text
F_L_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/F_L_ANTI_SCOPE_PROMPTS_REVISED.md
M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
PROMPTS_1_5.md -> docs/archive/development-history/root-prompt-packs/PROMPTS_1_5.md
R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
R_PHASE_ISSUE_PACK.md -> docs/archive/development-history/root-prompt-packs/R_PHASE_ISSUE_PACK.md
```

## What does not change

```text
docs/codex is not moved or deleted;
legacy stage checker scripts are not deleted;
legacy smoke tests are not mass-removed;
production readiness gate is not weakened;
product workflow pillars remain DOCX/PDF/XLSX/Slides/Python/Browser.
```

## Acceptance

KR-3F batch 1 is accepted only when:

```text
kw_controlled_archive_delete_readiness_check.py reports ready;
old root paths are absent;
archive paths are present;
active files outside the archive do not reference old root paths;
production readiness gate checks-only passes;
targeted tests pass;
full runner passes from committed project scripts;
Docker smoke passes from committed project scripts;
logs are archived under the repository logs directory;
remote branch contains the accepted commit.
```
