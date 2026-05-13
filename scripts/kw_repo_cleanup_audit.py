#!/usr/bin/env python3
"""Repository cleanup and portability audit for KW Studio.

This script is intentionally read-only. It does not delete, rename, move, or
rewrite project files. Its job is to produce a structured inventory before the
repository is simplified from development-stage history into a product-shaped
codebase.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

TEXT_SUFFIXES = {
    "",
    ".css",
    ".csv",
    ".dockerignore",
    ".env",
    ".example",
    ".gitignore",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

EXCLUDED_DIR_PARTS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "htmlcov",
    "logs",
    "node_modules",
    "playwright-report",
    "storage",
    "test-results",
}

STAGE_NAME_RE = re.compile(
    r"(?:^|[_/.-])(?:"
    r"s\d{1,2}[a-z]?|s_phase|"
    r"kq\d{1,2}[a-z]?|k_phase|"
    r"p\d{1,2}(?:_\d{1,2}[a-z]?)?|p_phase|"
    r"rc\d{1,2}|rch\d{1,2}|rf\d{1,2}|"
    r"krc|rc3|p10|s13"
    r")(?:[_/.-]|$)",
    re.IGNORECASE,
)

PRODUCT_WORKFLOWS: Mapping[str, Mapping[str, Sequence[str]]] = {
    "docx": {
        "required_docs": ("docs/workflows/DOCX_WORKFLOW.md",),
        "keywords": ("docx", "word"),
    },
    "pdf": {
        "required_docs": ("docs/workflows/PDF_WORKFLOW.md",),
        "keywords": ("pdf",),
    },
    "xlsx": {
        "required_docs": ("docs/workflows/XLSX_WORKFLOW.md", "docs/quality/XLSX_VALIDATION.md"),
        "keywords": ("xlsx", "excel", "spreadsheet", "workbook"),
    },
    "slides": {
        "required_docs": ("docs/workflows/SLIDES_WORKFLOW.md", "docs/quality/RENDER_AND_VISUAL_QA.md"),
        "keywords": ("slides", "pptx", "presentation"),
    },
    "python_analysis": {
        "required_docs": ("docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",),
        "keywords": ("python", "data_analysis", "analysis"),
    },
    "browser_evidence": {
        "required_docs": ("docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",),
        "keywords": ("browser", "evidence", "screenshot"),
    },
}

PORTABILITY_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "absolute_home_path": re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+(?:/|$)"),
    "profile_specific_label": re.compile(r"\bprofile\s*[12]\b|\bprofile[12]\b", re.IGNORECASE),
    "localized_downloads_path": re.compile(r"(?:/|\b)(?:Загрузки|Downloads)(?:/|\b)"),
    "active_branch_name": re.compile(r"\b[0-9]+_[A-Za-z0-9_]*Release_Hardening\b|\b9_Product_Release_Hardening\b"),
    "raw_git_sha": re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE),
}

PRODUCT_DOC_PREFIXES = (
    "docs/product/",
    "docs/architecture/",
    "docs/workflows/",
    "docs/quality/",
    "docs/operators/",
    "docs/refactor/",
)


@dataclass(frozen=True)
class FileClassification:
    path: str
    kind: str
    recommendation: str
    reason: str


@dataclass(frozen=True)
class PortabilityFinding:
    path: str
    line: int
    pattern: str
    snippet: str


@dataclass(frozen=True)
class WorkflowCoverage:
    workflow: str
    status: str
    present_docs: list[str]
    missing_docs: list[str]
    matching_files: list[str]


@dataclass
class CleanupAuditReport:
    generated_at: str
    repo_root: str
    summary: dict[str, int | str] = field(default_factory=dict)
    docs_inventory: list[FileClassification] = field(default_factory=list)
    tests_inventory: list[FileClassification] = field(default_factory=list)
    scripts_inventory: list[FileClassification] = field(default_factory=list)
    portability_findings: list[PortabilityFinding] = field(default_factory=list)
    workflow_coverage: list[WorkflowCoverage] = field(default_factory=list)


def _is_text_candidate(path: Path) -> bool:
    if path.name in {"Dockerfile", "Dockerfile.backend", "Makefile"}:
        return True
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.deploy.example")


def iter_project_files(repo_root: Path, *, max_file_size: int = 1_000_000) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in EXCLUDED_DIR_PARTS for part in rel.parts):
            continue
        if path.stat().st_size > max_file_size:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(repo_root).as_posix())


def iter_text_files(repo_root: Path, *, max_file_size: int = 1_000_000) -> list[Path]:
    return [path for path in iter_project_files(repo_root, max_file_size=max_file_size) if _is_text_candidate(path)]


def classify_doc(path: Path, repo_root: Path) -> FileClassification | None:
    rel = path.relative_to(repo_root).as_posix()
    if not rel.startswith("docs/") or path.suffix.lower() != ".md":
        return None
    if rel.startswith("docs/archive/"):
        return FileClassification(rel, "doc", "archived_legacy", "archived development history; not active product documentation")
    if rel.startswith(PRODUCT_DOC_PREFIXES):
        return FileClassification(rel, "doc", "keep_or_rewrite_as_product_doc", "active product documentation area")
    if rel.startswith("docs/codex/") or STAGE_NAME_RE.search(rel):
        return FileClassification(rel, "doc", "archive_or_delete", "stage-specific development history, not product-facing documentation")
    if "legacy" in rel.lower() or "migration" in rel.lower():
        return FileClassification(rel, "doc", "review_for_archive", "legacy or migration content should be compressed into operator/product docs")
    return FileClassification(rel, "doc", "review", "documentation outside the target product documentation structure")


def classify_test(path: Path, repo_root: Path) -> FileClassification | None:
    rel = path.relative_to(repo_root).as_posix()
    if not rel.startswith("backend/tests/") or path.suffix.lower() != ".py":
        return None
    if STAGE_NAME_RE.search(rel):
        return FileClassification(rel, "test", "rewrite_or_delete", "test name is tied to a development stage instead of product behavior")
    if "/smoke/" in rel:
        return FileClassification(rel, "test", "review_scope", "smoke test may be valid, but should map to a product or operator contract")
    return FileClassification(rel, "test", "keep_or_consolidate", "test appears product-oriented or layer-oriented")


def classify_script(path: Path, repo_root: Path) -> FileClassification | None:
    rel = path.relative_to(repo_root).as_posix()
    if not rel.startswith("scripts/") or path.suffix.lower() not in {".py", ".sh"}:
        return None
    if STAGE_NAME_RE.search(rel):
        return FileClassification(rel, "script", "archive_or_replace_with_product_tool", "script name is tied to a development stage")
    if rel.startswith("scripts/kw_"):
        return FileClassification(rel, "script", "keep_or_review", "operator/product script; verify it is path-neutral and still necessary")
    return FileClassification(rel, "script", "review", "script outside standard kw_ operator naming")


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def scan_portability(repo_root: Path, *, max_file_size: int = 1_000_000) -> list[PortabilityFinding]:
    findings: list[PortabilityFinding] = []
    for path in iter_text_files(repo_root, max_file_size=max_file_size):
        rel = path.relative_to(repo_root).as_posix()
        text = _safe_read_text(path)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PORTABILITY_PATTERNS.items():
                if pattern.search(line):
                    snippet = line.strip()
                    if len(snippet) > 220:
                        snippet = snippet[:217] + "..."
                    findings.append(PortabilityFinding(rel, line_no, name, snippet))
    return findings


def analyze_workflow_coverage(repo_root: Path, files: Iterable[Path]) -> list[WorkflowCoverage]:
    rel_files = [path.relative_to(repo_root).as_posix() for path in files]
    coverage: list[WorkflowCoverage] = []
    for workflow, spec in PRODUCT_WORKFLOWS.items():
        required_docs = list(spec["required_docs"])
        present_docs = [path for path in required_docs if (repo_root / path).exists()]
        missing_docs = [path for path in required_docs if not (repo_root / path).exists()]
        keywords = tuple(str(item).lower() for item in spec["keywords"])
        matching_files = [path for path in rel_files if any(keyword in path.lower() for keyword in keywords)]
        status = "ready" if not missing_docs and matching_files else "incomplete"
        coverage.append(
            WorkflowCoverage(
                workflow=workflow,
                status=status,
                present_docs=present_docs,
                missing_docs=missing_docs,
                matching_files=matching_files[:50],
            )
        )
    return coverage


def analyze_repository(repo_root: Path, *, max_file_size: int = 1_000_000) -> CleanupAuditReport:
    repo_root = repo_root.resolve()
    files = iter_project_files(repo_root, max_file_size=max_file_size)
    docs = [item for path in files if (item := classify_doc(path, repo_root)) is not None]
    tests = [item for path in files if (item := classify_test(path, repo_root)) is not None]
    scripts = [item for path in files if (item := classify_script(path, repo_root)) is not None]
    portability = scan_portability(repo_root, max_file_size=max_file_size)
    workflow_coverage = analyze_workflow_coverage(repo_root, files)

    summary: dict[str, int | str] = {
        "total_scanned_files": len(files),
        "docs_total": len(docs),
        "docs_archive_or_delete_candidates": sum(1 for item in docs if item.recommendation in {"archive_or_delete", "review_for_archive"}),
        "tests_total": len(tests),
        "tests_rewrite_or_delete_candidates": sum(1 for item in tests if item.recommendation == "rewrite_or_delete"),
        "scripts_total": len(scripts),
        "scripts_archive_or_replace_candidates": sum(1 for item in scripts if item.recommendation == "archive_or_replace_with_product_tool"),
        "portability_findings_total": len(portability),
        "workflow_count": len(workflow_coverage),
        "workflow_incomplete_count": sum(1 for item in workflow_coverage if item.status != "ready"),
    }

    return CleanupAuditReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        repo_root=str(repo_root),
        summary=summary,
        docs_inventory=docs,
        tests_inventory=tests,
        scripts_inventory=scripts,
        portability_findings=portability,
        workflow_coverage=workflow_coverage,
    )


def report_to_dict(report: CleanupAuditReport) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "repo_root": report.repo_root,
        "summary": report.summary,
        "docs_inventory": [asdict(item) for item in report.docs_inventory],
        "tests_inventory": [asdict(item) for item in report.tests_inventory],
        "scripts_inventory": [asdict(item) for item in report.scripts_inventory],
        "portability_findings": [asdict(item) for item in report.portability_findings],
        "workflow_coverage": [asdict(item) for item in report.workflow_coverage],
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _markdown_table(rows: Sequence[Sequence[object]], headers: Sequence[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(report: CleanupAuditReport) -> str:
    summary_rows = [(key, value) for key, value in sorted(report.summary.items())]
    workflow_rows = [
        (
            item.workflow,
            item.status,
            len(item.present_docs),
            len(item.missing_docs),
            len(item.matching_files),
        )
        for item in report.workflow_coverage
    ]
    doc_rows = [(item.path, item.recommendation, item.reason) for item in report.docs_inventory[:100]]
    test_rows = [(item.path, item.recommendation, item.reason) for item in report.tests_inventory[:100]]
    script_rows = [(item.path, item.recommendation, item.reason) for item in report.scripts_inventory[:100]]
    portability_rows = [
        (item.path, item.line, item.pattern, item.snippet) for item in report.portability_findings[:100]
    ]

    return "\n\n".join(
        [
            "# Repository cleanup audit",
            "This report is generated by `scripts/kw_repo_cleanup_audit.py`. It is read-only and is intended to guide product cleanup before deleting or rewriting files.",
            "## Summary\n\n" + _markdown_table(summary_rows, ("Metric", "Value")),
            "## Workflow coverage\n\n" + _markdown_table(workflow_rows, ("Workflow", "Status", "Present docs", "Missing docs", "Matching files")),
            "## Documentation inventory, first 100\n\n" + _markdown_table(doc_rows, ("Path", "Recommendation", "Reason")),
            "## Test inventory, first 100\n\n" + _markdown_table(test_rows, ("Path", "Recommendation", "Reason")),
            "## Script inventory, first 100\n\n" + _markdown_table(script_rows, ("Path", "Recommendation", "Reason")),
            "## Portability findings, first 100\n\n" + _markdown_table(portability_rows, ("Path", "Line", "Pattern", "Snippet")),
            "## Next step\n\nUse this inventory to build a controlled cleanup patch. Do not delete files based on this report alone without reviewing the categories and preserving product-critical gates.",
        ]
    ) + "\n"


def write_report_outputs(report: CleanupAuditReport, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = report_to_dict(report)
    written: list[Path] = []

    targets = {
        "cleanup_inventory.json": payload,
        "docs_inventory.json": [asdict(item) for item in report.docs_inventory],
        "test_inventory.json": [asdict(item) for item in report.tests_inventory],
        "scripts_inventory.json": [asdict(item) for item in report.scripts_inventory],
        "path_portability_findings.json": [asdict(item) for item in report.portability_findings],
        "workflow_coverage.json": [asdict(item) for item in report.workflow_coverage],
    }
    for name, value in targets.items():
        path = output_dir / name
        _write_json(path, value)
        written.append(path)

    md_path = output_dir / "cleanup_inventory.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    written.append(md_path)
    return written


def make_zip(output_files: Sequence[Path], zip_path: Path, *, base_dir: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in output_files:
            archive.write(path, path.relative_to(base_dir).as_posix())
    return zip_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit KW Studio repository cleanup and portability candidates.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root. Defaults to current directory.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for JSON/Markdown report files.")
    parser.add_argument("--zip-out", type=Path, default=None, help="Optional ZIP path for generated reports.")
    parser.add_argument("--max-file-size", type=int, default=1_000_000, help="Skip files larger than this many bytes.")
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")

    report = analyze_repository(repo_root, max_file_size=args.max_file_size)
    output_dir = args.output_dir or (repo_root / "logs" / "repository-cleanup-audit")
    output_files = write_report_outputs(report, output_dir)

    zip_path = None
    if args.zip_out:
        zip_path = make_zip(output_files, args.zip_out.resolve(), base_dir=output_dir)

    if args.json:
        print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print(f"[INFO] output_dir={output_dir}")
        if zip_path:
            print(f"[INFO] zip_out={zip_path}")
        print(f"[INFO] portability_findings={len(report.portability_findings)}")
        print(f"[INFO] workflow_incomplete_count={report.summary['workflow_incomplete_count']}")
        print("[PASS] repository cleanup audit completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
