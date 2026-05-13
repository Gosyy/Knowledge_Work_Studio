# KR-0B Repository Cleanup Policy and Rewrite Map

KR-0B converts the KR-0A audit inventory into a controlled cleanup policy. It is deliberately non-destructive: it does not remove documentation, tests, scripts, or code. Its purpose is to make the next cleanup patches safe and product-oriented.

## Product direction

KW Studio is an offline/intranet, artifact-first knowledge-work studio for these first-class workflows:

- DOCX
- PDF
- XLSX / Excel
- Slides
- Python analysis
- Browser-assisted evidence workflows

The repository should describe and test those workflows directly. Active code, documentation, scripts, and tests should not be named around temporary phase labels such as S13, P10, RF, RC, KQ, or around local operator machines such as profile 1/profile 2.

## Why this policy exists

During the S, KQ, and release-hardening phases, the repository accumulated many files whose names and contents were useful as development evidence, but not as long-term product structure. Examples include patch-verdict documentation, stage-specific smoke tests, one-off operator scripts, and commands tied to a specific local path.

That history helped us reach a stable baseline. It should not remain the active interface of the product.

## Cleanup actions

KR-0B assigns each audited item one of these actions:

| Action | Meaning |
| --- | --- |
| `keep` | Keep as active product code, test, or documentation. |
| `rewrite` | Preserve the intent, but rewrite under product workflow names and path-neutral assumptions. |
| `archive` | Move to development-history archive or remove from active gates before later deletion. |
| `delete` | Delete only when there is no durable product value and no active gate dependency. |
| `rename` | Rename stage-specific modules/scripts to product-level names, with compatibility shims when needed. |
| `path_neutralize` | Remove local user, profile, branch, commit, or absolute-path assumptions. |

## Rules for future cleanup patches

1. Archive before delete when a file may still be referenced by readiness gates, CI, or operator scripts.
2. Do not rename a module without updating tests and operator scripts in the same patch.
3. Active documentation must describe the product and its workflows, not patch history.
4. Active tests must verify product contracts, not branch names, commit SHAs, or local profile paths.
5. XLSX/Excel is mandatory and must have workflow documentation, validation documentation, and tests.
6. All paths in active code/tests must be repository-relative, argument-driven, environment-driven, or temporary-test paths.
7. Profile-specific commands may appear only in user-facing one-off chat instructions, not in committed code or active docs.

## Target documentation surface

The intended active documentation surface is:

```text
docs/product/
  PRODUCT_VISION.md
  USER_WORKFLOWS.md
  ARTIFACT_MODEL.md

docs/architecture/
  SYSTEM_ARCHITECTURE.md
  OFFLINE_LLM_TOPOLOGY.md
  STORAGE_AND_METADATA.md
  TOOL_AND_WORKFLOW_CONTRACTS.md

docs/workflows/
  DOCX_WORKFLOW.md
  PDF_WORKFLOW.md
  XLSX_WORKFLOW.md
  SLIDES_WORKFLOW.md
  PYTHON_ANALYSIS_WORKFLOW.md
  BROWSER_EVIDENCE_WORKFLOW.md

docs/quality/
  QUALITY_GATES.md
  PROVENANCE_AND_CITATIONS.md
  RENDER_AND_VISUAL_QA.md
  XLSX_VALIDATION.md

docs/operators/
  LOCAL_DEVELOPMENT.md
  DEPLOYMENT.md
  BACKUP_RESTORE.md
  DIAGNOSTICS.md
```

## Target test surface

The intended active test surface is organized by product behavior:

```text
backend/tests/api/
backend/tests/workflows/
backend/tests/quality/
backend/tests/integrations/
backend/tests/operators/
```

Stage-specific smoke tests should be rewritten into workflow or quality tests, then removed from active gates.

## KR-0B tooling

Use `scripts/kw_repo_cleanup_policy.py` with a KR-0A audit output:

```bash
python3 scripts/kw_repo_cleanup_policy.py \
  --audit-zip logs/kr0a-repository-cleanup-audit-report.zip \
  --output-dir logs/kr0b-cleanup-policy \
  --zip-out logs/kr0b-cleanup-policy.zip \
  --json
```

Generated files:

- `cleanup_policy.json`
- `cleanup_policy.md`
- `rename_plan.json`
- `path_neutralization_plan.json`
- `workflow_rewrite_plan.json`

## Recommended next patches

- KR-1A: create the canonical product documentation skeleton.
- KR-1B: archive obsolete stage documentation after KR-1A exists.
- KR-2A: rewrite stage smoke tests into product contract tests.
- KR-3A: remove profile/path/branch/commit assumptions from active files.
- KR-4A: introduce shared workflow contracts.
- KR-5A: add XLSX first-class workflow documentation, validation, and tests.
