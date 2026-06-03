#!/usr/bin/env python3
"""Validate KW Studio assistant decision-governance documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = [
    "docs/ASSISTANT_OPERATING_RULES.md",
    "docs/DEFINITION_OF_DONE.md",
    "docs/PROJECT_PROHIBITIONS.md",
    "docs/QUALITY_MATRIX.md",
    "docs/adr/0001-assistant-decision-governance.md",
    "docs/adr/0002-product-slice-quality-gate.md",
    "docs/templates/PRE_PATCH_REPORT_TEMPLATE.md",
    "docs/templates/POST_PATCH_REPORT_TEMPLATE.md",
    "docs/templates/LOG_ANALYSIS_TEMPLATE.md",
]

REQUIRED_LINKS = {
    "AGENTS.md": [
        "docs/ASSISTANT_OPERATING_RULES.md",
        "docs/DEFINITION_OF_DONE.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
        "Assistant decision governance",
        "documentation stewardship",
    ],
    "docs/refactor/CODEX_PROJECT_BRIEFING.md": [
        "docs/ASSISTANT_OPERATING_RULES.md",
        "docs/DEFINITION_OF_DONE.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "Assistant Decision Governance",
        "docs/ASSISTANT_OPERATING_RULES.md",
        "docs/DEFINITION_OF_DONE.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
        "docs/templates/PRE_PATCH_REPORT_TEMPLATE.md",
        "docs/templates/POST_PATCH_REPORT_TEMPLATE.md",
        "docs/templates/LOG_ANALYSIS_TEMPLATE.md",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "Assistant Decision Governance",
        "scripts/kw_assistant_governance_check.py",
    ],
    "README.md": [
        "docs/ASSISTANT_OPERATING_RULES.md",
        "docs/DEFINITION_OF_DONE.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "kw_assistant_governance_check.py",
    ],
}

REQUIRED_PHRASES = {
    "docs/ASSISTANT_OPERATING_RULES.md": [
        "Mandatory local preflight",
        "Mandatory `.venv` rule",
        "Documentation stewardship rules",
        "Mandatory vertical product-slice rule",
        "docs/templates/PRE_PATCH_REPORT_TEMPLATE.md",
        "docs/templates/POST_PATCH_REPORT_TEMPLATE.md",
        "docs/templates/LOG_ANALYSIS_TEMPLATE.md",
    ],
    "docs/DEFINITION_OF_DONE.md": [
        "Patch-level DONE",
        "Local acceptance",
        "Remote acceptance",
        "Documentation DONE",
        "Tests passing is necessary but not sufficient",
        "Product-slice DONE",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "issue code patches without a verified local full-history checkout",
        "silently replace failed LLM generation with fallback content",
        "leave original template text in a full-rewrite presentation mode",
        "claim Kimi-level quality without quality gates and evidence",
        "close a roadmap phase with only an isolated contract/checker module",
    ],
    "docs/QUALITY_MATRIX.md": [
        "DOCX",
        "PDF",
        "XLSX / CSV",
        "Slides",
        "Python analysis",
        "Browser evidence",
        "Documentation maintenance rule",
        "Product-slice quality gate",
    ],
    "docs/adr/0001-assistant-decision-governance.md": [
        "Status",
        "Accepted",
        "Decision",
        "Rejected alternatives",
    ],
    "docs/adr/0002-product-slice-quality-gate.md": [
        "Status",
        "Accepted",
        "Product Slice Quality Gate",
        "vertical product slice",
        "Rejected alternatives",
    ],
}


def _missing_phrases(text: str, phrases: Iterable[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase not in text]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_report(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    issues: list[str] = []
    missing_files: list[str] = []
    missing_links: dict[str, list[str]] = {}
    missing_required_phrases: dict[str, list[str]] = {}

    for rel_path in REQUIRED_FILES:
        path = repo_root / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            issues.append(f"missing required governance file: {rel_path}")

    for rel_path, phrases in REQUIRED_LINKS.items():
        text = _read_text(repo_root / rel_path)
        if not text:
            missing_links[rel_path] = phrases
            issues.append(f"missing file checked for governance links: {rel_path}")
            continue
        missing = _missing_phrases(text, phrases)
        if missing:
            missing_links[rel_path] = missing
            issues.extend(f"{rel_path} missing governance link/phrase: {phrase}" for phrase in missing)

    for rel_path, phrases in REQUIRED_PHRASES.items():
        text = _read_text(repo_root / rel_path)
        missing = _missing_phrases(text, phrases)
        if missing:
            missing_required_phrases[rel_path] = missing
            issues.extend(f"{rel_path} missing required phrase: {phrase}" for phrase in missing)

    return {
        "status": "ready" if not issues else "not_ready",
        "required_files_checked": len(REQUIRED_FILES),
        "required_link_files_checked": len(REQUIRED_LINKS),
        "required_phrase_files_checked": len(REQUIRED_PHRASES),
        "missing_files": missing_files,
        "missing_links": missing_links,
        "missing_required_phrases": missing_required_phrases,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless governance is ready.")
    args = parser.parse_args()

    report = build_report(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Assistant governance status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
