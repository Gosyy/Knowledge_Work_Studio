# Python Analysis Workflow

The Python analysis workflow runs reproducible analysis over files and extracted data.

## Goals

- Analyze CSV, XLSX, PDF-extracted tables, JSON, and other structured data.
- Produce tables, charts, metrics, and diagnostics.
- Record execution inputs and generated outputs.
- Make results reusable by DOCX, PDF, XLSX, and Slides workflows.

## Expected artifacts

- `analysis_report.json` or Markdown report.
- Generated tables and charts.
- Input data manifest.
- Execution summary.
- Optional cleaned or transformed datasets.

## Quality checks

- Inputs are recorded.
- Generated files are listed in a manifest.
- Failures are explicit.
- Charts and tables can be traced to data inputs.
- No notebook/kernel path assumptions are required for review.
