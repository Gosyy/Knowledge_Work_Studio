#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CANONICAL_PRODUCT_DOCS: tuple[str, ...] = (
    "docs/product/PRODUCT_VISION.md",
    "docs/product/USER_WORKFLOWS.md",
    "docs/product/ARTIFACT_MODEL.md",
    "docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md",
    "docs/workflows/DOCX_WORKFLOW.md",
    "docs/workflows/PDF_WORKFLOW.md",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
    "docs/quality/QUALITY_GATES.md",
    "docs/quality/XLSX_VALIDATION.md",
    "docs/quality/RENDER_AND_VISUAL_QA.md",
    "docs/operators/LOCAL_DEVELOPMENT.md",
)

POLICY_DOCS: tuple[str, ...] = (
    "docs/archive/development-history/README.md",
    "docs/refactor/STAGE_DOCUMENTATION_DEPRECATION_INDEX.md",
)

MANDATORY_WORKFLOWS: tuple[str, ...] = (
    "DOCX",
    "PDF",
    "XLSX",
    "Slides",
    "Python analysis",
    "Browser evidence",
)

STAGE_DOC_PATTERN = re.compile(
    r"^(P\d|P_PHASE|K\d|K_PHASE|KQ|KRC|RC\d|RCH\d|RF|S\d|S_PHASE|OFFLINE_|SLIDES_|DOCX_PDF_|GIGACHAT_|RUNTIME_|CONTROLLED_)",
    re.IGNORECASE,
)

STAGE_DIRECTORY = Path("docs/codex")
ARCHIVE_DIRECTORY = Path("docs/archive/development-history")


@dataclass(frozen=True)
class FileCheck:
    path: str
    exists: bool
    status: str
    issues: list[str]


@dataclass(frozen=True)
class DeprecationReport:
    status: str
    repo_root: str
    canonical_docs: list[FileCheck]
    policy_docs: list[FileCheck]
    legacy_stage_docs_count: int
    legacy_stage_docs_sample: list[str]
    mandatory_workflows: list[str]
    physical_archive_blocked_until: str
    issues: list[str]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _check_required_file(repo_root: Path, rel_path: str, required_phrases: Iterable[str] = ()) -> FileCheck:
    path = repo_root / rel_path
    issues: list[str] = []
    if not path.exists():
        return FileCheck(path=rel_path, exists=False, status="missing", issues=["file is missing"])
    if not path.is_file():
        return FileCheck(path=rel_path, exists=True, status="invalid", issues=["path is not a file"])
    content = _read_text(path)
    if "/home/editor" in content or "Profile 2" in content or "profile2" in content:
        issues.append("file contains machine/profile-specific wording")
    for phrase in required_phrases:
        if phrase not in content:
            issues.append(f"missing required phrase: {phrase}")
    return FileCheck(path=rel_path, exists=True, status="ready" if not issues else "issues", issues=issues)


def _stage_docs(repo_root: Path) -> list[str]:
    codex_dir = repo_root / STAGE_DIRECTORY
    if not codex_dir.exists():
        return []
    docs: list[str] = []
    for path in codex_dir.rglob("*.md"):
        rel = path.relative_to(repo_root).as_posix()
        if STAGE_DOC_PATTERN.search(path.name):
            docs.append(rel)
    return sorted(docs)


def _write_outputs(report: DeprecationReport, output_dir: Path | None, zip_out: Path | None) -> None:
    if output_dir is None and zip_out is None:
        return
    if output_dir is None:
        output_dir = Path.cwd() / "stage-docs-deprecation-report"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "stage_docs_deprecation_report.json"
    md_path = output_dir / "stage_docs_deprecation_report.md"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Stage Documentation Deprecation Report",
        "",
        f"Status: `{report.status}`",
        f"Legacy stage docs still in `docs/codex`: `{report.legacy_stage_docs_count}`",
        f"Physical archive blocked until: `{report.physical_archive_blocked_until}`",
        "",
        "## Mandatory product workflows",
        "",
    ]
    lines.extend(f"- {workflow}" for workflow in report.mandatory_workflows)
    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(f"- {issue}" for issue in report.issues)
    else:
        lines.append("- none")
    lines.extend(["", "## Legacy stage doc sample", ""])
    lines.extend(f"- `{path}`" for path in report.legacy_stage_docs_sample[:50])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if zip_out is not None:
        zip_out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(output_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(output_dir))


def build_report(repo_root: Path) -> DeprecationReport:
    repo_root = repo_root.resolve()
    issues: list[str] = []

    canonical = [_check_required_file(repo_root, path) for path in CANONICAL_PRODUCT_DOCS]
    for item in canonical:
        issues.extend(f"{item.path}: {issue}" for issue in item.issues)
        if not item.exists:
            issues.append(f"missing canonical product doc: {item.path}")

    policy_required_phrases = (
        "docs/codex remains temporarily for legacy tests/checkers",
        "KR-2",
        "Canonical product docs",
    )
    policy = [
        _check_required_file(repo_root, POLICY_DOCS[0], policy_required_phrases),
        _check_required_file(repo_root, POLICY_DOCS[1], policy_required_phrases),
    ]
    for item in policy:
        issues.extend(f"{item.path}: {issue}" for issue in item.issues)
        if not item.exists:
            issues.append(f"missing deprecation policy doc: {item.path}")

    stage_docs = _stage_docs(repo_root)
    if not (repo_root / STAGE_DIRECTORY).exists():
        issues.append("docs/codex is missing; physical stage-doc archive must wait until KR-2 rewrites legacy checkers")

    status = "ready" if not issues else "needs_attention"
    return DeprecationReport(
        status=status,
        repo_root=str(repo_root),
        canonical_docs=canonical,
        policy_docs=policy,
        legacy_stage_docs_count=len(stage_docs),
        legacy_stage_docs_sample=stage_docs[:100],
        mandatory_workflows=list(MANDATORY_WORKFLOWS),
        physical_archive_blocked_until="KR-2 rewrites stage-specific tests and checker scripts",
        issues=issues,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-1B-R2 stage documentation deprecation policy.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--output-dir", help="Optional directory for JSON/Markdown report artifacts.")
    parser.add_argument("--zip-out", help="Optional ZIP path for report artifacts.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless report status is ready.")
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(Path(args.repo_root))
    _write_outputs(
        report,
        Path(args.output_dir) if args.output_dir else None,
        Path(args.zip_out) if args.zip_out else None,
    )
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(f"status={report.status}")
        print(f"legacy_stage_docs_count={report.legacy_stage_docs_count}")
    if args.require_ready and report.status != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
