#!/usr/bin/env python3
"""Validate KW Studio product-slice quality governance.

This checker prevents post-foundation KR work from silently drifting into
isolated contract-only layers without a roadmap integration plan.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_PHRASES: dict[str, list[str]] = {
    "docs/ASSISTANT_OPERATING_RULES.md": [
        "Mandatory vertical product-slice rule",
        "small vertical product slices over isolated contract-only layers",
        "user-visible or artifact-visible workflow outcome",
    ],
    "docs/DEFINITION_OF_DONE.md": [
        "Product-slice DONE",
        "A patch that only introduces a disconnected contract layer is `TARGETED PASS` at most",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "Product-slice quality prohibitions",
        "close a roadmap phase with only an isolated contract/checker module",
    ],
    "docs/QUALITY_MATRIX.md": [
        "Product-slice quality gate",
        "isolated schemas/checkers as foundation evidence, not as final product quality",
    ],
    "docs/adr/0002-product-slice-quality-gate.md": [
        "ADR 0002: Product Slice Quality Gate",
        "Accepted",
        "vertical product slice",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7O re-baseline — product-slice quality mandate",
        "Required remediation for KR-7I through KR-7N",
        "KR-7O scenario packs must therefore not be closed as only `presentation_scenario_packs.v1`",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "Product-slice re-baseline after KR-7N",
        "post-KR-7H patches must prefer vertical product slices over isolated contracts",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "Product-slice governance update after KR-7N",
        "KR-7O must be re-planned as scenario-pack integration work",
    ],
    "docs/templates/PRE_PATCH_REPORT_TEMPLATE.md": [
        "Vertical product-slice requirement",
        "User-visible or artifact-visible outcome changed",
    ],
    "docs/templates/POST_PATCH_REPORT_TEMPLATE.md": [
        "Product-slice evidence",
        "Integrated product path",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "kw_product_slice_governance_check.py",
    ],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def build_report(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    issues: list[str] = []
    checked: dict[str, list[str]] = {}

    for rel_path, phrases in REQUIRED_PHRASES.items():
        text = read_text(repo_root / rel_path)
        missing = [phrase for phrase in phrases if phrase not in text]
        checked[rel_path] = phrases
        if not text:
            issues.append(f"missing required product-slice governance file: {rel_path}")
        for phrase in missing:
            issues.append(f"{rel_path} missing required phrase: {phrase}")

    return {
        "schema_version": "kw_product_slice_governance_check.v1",
        "status": "ready" if not issues else "not_ready",
        "product_slice_governance_required": True,
        "contract_only_phase_closure_forbidden": True,
        "vertical_product_slice_required_after_foundation_gate": True,
        "checked_files": sorted(checked),
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
        print(f"Product-slice governance status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
