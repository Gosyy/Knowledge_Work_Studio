# Repository cleanup audit

KW Studio is being realigned from a stage-heavy development repository into a product-shaped, portable, offline/intranet knowledge-work studio.

The product direction is:

- DOCX workflows
- PDF workflows
- XLSX/Excel workflows
- Slides workflows
- Python analysis workflows
- Browser-assisted evidence workflows

The cleanup must be controlled. The first step is not deletion. The first step is an inventory that identifies which files are product-facing, which files are development history, which tests are tied to old stages, and which code or documentation contains machine-specific assumptions.

## Audit tool

Run:

```bash
python3 scripts/kw_repo_cleanup_audit.py \
  --repo-root . \
  --output-dir logs/repository-cleanup-audit \
  --zip-out logs/repository-cleanup-audit.zip \
  --json
```

The tool writes:

- `cleanup_inventory.json`
- `cleanup_inventory.md`
- `docs_inventory.json`
- `test_inventory.json`
- `scripts_inventory.json`
- `path_portability_findings.json`
- `workflow_coverage.json`

The tool is read-only. It does not delete, move, rename, or rewrite files.

## What the audit is looking for

The audit highlights:

- documentation that should become product documentation or be archived;
- tests tied to historical stages instead of product behavior;
- scripts tied to historical stages instead of reusable operator tools;
- absolute local paths, profile-specific names, localized Downloads paths, branch names, and raw commit SHA references;
- missing workflow documentation for required product workflows, including XLSX/Excel.

## Follow-up policy

Do not delete files directly from the audit result without review. The intended sequence is:

1. Generate the cleanup inventory.
2. Review keep/archive/delete categories.
3. Replace stage-specific documentation with product documentation.
4. Replace stage-specific tests with product workflow tests.
5. Fix path portability issues.
6. Run the full test runner and Docker smoke on a clean committed branch.
