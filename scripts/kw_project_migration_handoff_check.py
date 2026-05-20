#!/usr/bin/env python3
"""Validate the KW Studio project migration handoff document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


HANDOFF_PATH = Path("docs/refactor/PROJECT_MIGRATION_HANDOFF.md")
ROADMAP_PATH = Path("docs/refactor/KR_PRODUCT_RESET_ROADMAP.md")

REQUIRED_PHRASES = [
    "profile3_ubuntu2604_terminal_theme.sh",
    "profile3_ubuntu2604_project_bootstrap.sh",
    "VMware Workstation 17 Pro",
    "Ubuntu 26.04 LTS",
    "Profile 3 local-only paths",
    "Update rule:",
    "Every future patch must review and update this file",
    "especially after the user and assistant agree on a new phase plan",
    "offline/intranet",
    "artifact-first",
    "provenance-first",
    "operator-gated",
    "DOCX workflow",
    "PDF workflow",
    "XLSX / Excel workflow",
    "Slides workflow",
    "Python analysis workflow",
    "Browser-assisted evidence workflow",
    "Current accepted continuation status",
    "KR-4A",
    "KR-5A",
    "WorkflowInput",
    "WorkflowPlan",
    "WorkflowManifest",
    "WorkflowQualityReport",
    "WorkflowProvenance",
    "project-resident",
    "full runner",
    "Docker smoke",
    "logs",
    "git apply --check",
    "py_compile",
    "targeted pytest",
    "ACCEPT",
    "docs/codex",
    "GigaChat",
    "LibreOffice",
    "Profile 1 local-only paths",
    "Profile 2 local-only paths",
    "After every agreed new phase plan, update docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
    "Profile-neutral runner resource limits",
    "KWS_NOFILE_LIMIT",
    "Profile-neutral SQLite repository directory hotfix",
    "Profile-neutral operation rule",
    "Profile 1 and Profile 3 are parallel working profiles",
    "The project must not depend on a single main profile",
    "scripts/bootstrap/profile3_ubuntu2604_project_bootstrap.sh",
    "scripts/bootstrap/profile3_ubuntu2604_terminal_theme.sh",
]

ROADMAP_REQUIRED_PHRASES = [
    "PROJECT_MIGRATION_HANDOFF.md",
    "handoff",
    "new phase plan",
]


def missing_phrases(text: str, phrases: Iterable[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase not in text]


def build_report(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    handoff = repo_root / HANDOFF_PATH
    roadmap = repo_root / ROADMAP_PATH

    handoff_text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""
    roadmap_text = roadmap.read_text(encoding="utf-8") if roadmap.exists() else ""

    missing = missing_phrases(handoff_text, REQUIRED_PHRASES)
    roadmap_missing = missing_phrases(roadmap_text, ROADMAP_REQUIRED_PHRASES)

    issues: list[str] = []
    if not handoff.exists():
        issues.append(f"missing handoff document: {HANDOFF_PATH.as_posix()}")
    if not roadmap.exists():
        issues.append(f"missing roadmap document: {ROADMAP_PATH.as_posix()}")
    issues.extend(f"handoff missing phrase: {phrase}" for phrase in missing)
    issues.extend(f"roadmap missing phrase: {phrase}" for phrase in roadmap_missing)

    return {
        "status": "ready" if not issues else "not_ready",
        "handoff_path": HANDOFF_PATH.as_posix(),
        "roadmap_path": ROADMAP_PATH.as_posix(),
        "required_phrases_checked": len(REQUIRED_PHRASES),
        "roadmap_required_phrases_checked": len(ROADMAP_REQUIRED_PHRASES),
        "missing_required_phrases": missing,
        "missing_roadmap_phrases": roadmap_missing,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the report is ready.")
    args = parser.parse_args()

    report = build_report(Path(args.repo_root))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Project migration handoff status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
