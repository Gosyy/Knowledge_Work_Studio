#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_DOCS = {
    "product_vision": "docs/product/PRODUCT_VISION.md",
    "user_workflows": "docs/product/USER_WORKFLOWS.md",
    "artifact_model": "docs/product/ARTIFACT_MODEL.md",
    "tool_contracts": "docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md",
    "docx_workflow": "docs/workflows/DOCX_WORKFLOW.md",
    "pdf_workflow": "docs/workflows/PDF_WORKFLOW.md",
    "xlsx_workflow": "docs/workflows/XLSX_WORKFLOW.md",
    "slides_workflow": "docs/workflows/SLIDES_WORKFLOW.md",
    "python_analysis_workflow": "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "browser_evidence_workflow": "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
    "quality_gates": "docs/quality/QUALITY_GATES.md",
    "xlsx_validation": "docs/quality/XLSX_VALIDATION.md",
    "render_visual_qa": "docs/quality/RENDER_AND_VISUAL_QA.md",
    "local_development": "docs/operators/LOCAL_DEVELOPMENT.md",
}

MANDATORY_WORKFLOWS = (
    "DOCX",
    "PDF",
    "XLSX",
    "Slides",
    "Python analysis",
    "Browser",
)

FORBIDDEN_ACTIVE_DOC_MARKERS = (
    "/home/editor",
    "Profile 1",
    "Profile 2",
    "profile1",
    "profile2",
    "Загрузки",
)

@dataclass(frozen=True)
class DocCheck:
    key: str
    path: str
    exists: bool
    status: str
    issues: tuple[str, ...]


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_doc(repo_root: Path, key: str, relative_path: str) -> DocCheck:
    path = repo_root / relative_path
    issues: list[str] = []
    if not path.exists():
        return DocCheck(key=key, path=relative_path, exists=False, status="missing", issues=("file is missing",))
    text = _read_text(path)
    if len(text.strip()) < 200:
        issues.append("document is too small to be useful")
    for marker in FORBIDDEN_ACTIVE_DOC_MARKERS:
        if marker in text:
            issues.append(f"contains path/profile-specific marker: {marker}")
    return DocCheck(
        key=key,
        path=relative_path,
        exists=True,
        status="ready" if not issues else "needs_work",
        issues=tuple(issues),
    )


def build_report(repo_root: Path) -> dict[str, Any]:
    checks = [check_required_doc(repo_root, key, path) for key, path in REQUIRED_DOCS.items()]
    workflow_text = "\n".join(
        _read_text(repo_root / REQUIRED_DOCS[key])
        for key in REQUIRED_DOCS
        if (repo_root / REQUIRED_DOCS[key]).exists()
    )
    missing_workflows = [workflow for workflow in MANDATORY_WORKFLOWS if workflow not in workflow_text]
    issues = [f"{check.path}: {issue}" for check in checks for issue in check.issues]
    for workflow in missing_workflows:
        issues.append(f"mandatory workflow not documented: {workflow}")
    status = "ready" if not issues else "needs_work"
    return {
        "status": status,
        "required_doc_count": len(REQUIRED_DOCS),
        "ready_doc_count": sum(1 for check in checks if check.status == "ready"),
        "missing_doc_count": sum(1 for check in checks if not check.exists),
        "mandatory_workflows": list(MANDATORY_WORKFLOWS),
        "missing_workflows": missing_workflows,
        "checks": [check.__dict__ for check in checks],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check canonical KW Studio product documentation skeleton.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"KW product docs status: {report['status']}")
        print(f"required docs: {report['required_doc_count']}")
        print(f"ready docs: {report['ready_doc_count']}")
        if report["issues"]:
            print("Issues:")
            for issue in report["issues"]:
                print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
