#!/usr/bin/env python3
"""Validate the KR Product Reset Roadmap anchor document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


REQUIRED_PHRASES = [
    "artifact-first",
    "provenance-first",
    "operator-gated",
    "offline/intranet",
    "DOCX workflow",
    "PDF workflow",
    "XLSX / Excel workflow",
    "Slides workflow",
    "Python analysis workflow",
    "Browser-assisted evidence workflow",
    "WorkflowInput",
    "WorkflowPlan",
    "WorkflowManifest",
    "WorkflowQualityReport",
    "WorkflowProvenance",
    "KR-3E",
    "KR-4A",
    "KR-5A",
    "KR-5B",
    "KR-6A",
    "full runner",
    "Docker smoke",
    "GigaChat",
]

FORBIDDEN_PHRASES = [
    "npm audit fix --force without a controlled dependency/security patch",
]


def find_missing(text: str, phrases: Iterable[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase not in text]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the report is ready.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    roadmap = repo_root / "docs" / "refactor" / "KR_PRODUCT_RESET_ROADMAP.md"

    if roadmap.exists():
        text = roadmap.read_text(encoding="utf-8")
        missing = find_missing(text, REQUIRED_PHRASES)
        forbidden_present = [phrase for phrase in FORBIDDEN_PHRASES if phrase not in text]
    else:
        text = ""
        missing = [str(roadmap)] + REQUIRED_PHRASES
        forbidden_present = []

    report = {
        "status": "ready" if roadmap.exists() and not missing and not forbidden_present else "not_ready",
        "roadmap": str(roadmap.relative_to(repo_root)) if roadmap.exists() else str(roadmap),
        "required_phrases_checked": len(REQUIRED_PHRASES),
        "missing_required_phrases": missing,
        "forbidden_policy_text_missing": forbidden_present,
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"KR product reset roadmap status: {report['status']}")
        if missing:
            print("Missing required phrases:")
            for phrase in missing:
                print(f"- {phrase}")
        if forbidden_present:
            print("Missing explicit forbidden-policy text:")
            for phrase in forbidden_present:
                print(f"- {phrase}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
