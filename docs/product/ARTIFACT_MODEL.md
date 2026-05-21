# Artifact Model

KW Studio treats generated work as artifact bundles rather than isolated files. A bundle is a directory or ZIP that contains outputs plus enough metadata to validate and review them.

## Required bundle concepts

- **Primary artifact**: the main user-facing file, such as `.docx`, `.pdf`, `.xlsx`, `.pptx`, `.html`, `.csv`, or `.json`.
- **Manifest**: machine-readable description of generated files, source inputs, workflow type, timestamps, and generator version.
- **Quality report**: result of validation checks. Examples: OOXML validity, workbook formula checks, render QA, geometry checks, extraction status.
- **Provenance manifest**: maps generated claims, slides, tables, charts, or paragraphs to source material.
- **Review packet**: human-readable summary of what was produced, what evidence supports it, and what still requires review.
- **Logs**: operator/debug evidence, archived separately and redacted for secrets.

## Bundle requirements

Every workflow bundle should answer these questions:

1. What did we generate?
2. What inputs did we use?
3. What validation was performed?
4. What evidence supports the result?
5. What are the known limitations?
6. How can an operator reproduce or inspect the run?

## Portability requirement

Bundle contents must use relative paths where possible. Manifests must not require a specific checkout directory, Linux username, profile number, branch name, or commit hash to be useful.
