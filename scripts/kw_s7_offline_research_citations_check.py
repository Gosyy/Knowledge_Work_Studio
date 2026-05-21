#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.offline_research_citations import offline_research_citations_report  # noqa: E402

EXPECTED_BASE_AFTER_S6 = "7a0e6732429b6fc9e29e78ef49453f6715f320d3"
REQUIRED_FILES = (
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S6_IMAGE_SCREENSHOT_TO_SLIDE_WORKFLOW.md",
    "docs/codex/S7_OFFLINE_INTRANET_RESEARCH_CITATIONS.md",
    "backend/app/services/slides_service/native_visuals.py",
    "backend/app/services/slides_service/image_to_slide_workflow.py",
    "backend/app/services/slides_service/offline_research_citations.py",
    "scripts/kw_s6_image_to_slide_workflow_check.py",
    "scripts/kw_s7_offline_research_citations_check.py",
    "backend/tests/smoke/test_s7_offline_research_citations.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S7 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S6:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S6, head)
            if ancestry is False:
                errors.append(f"expected S6 baseline {EXPECTED_BASE_AFTER_S6} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S6 ancestry for {EXPECTED_BASE_AFTER_S6}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    report = offline_research_citations_report()
    errors = list(report.get("errors", []))
    errors.extend(collect_static_errors(repo_root, require_ready))
    report["repo_root"] = str(repo_root)
    report["required_paths"] = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    report["expected_base_after_s6"] = EXPECTED_BASE_AFTER_S6
    report["branch"] = run_git(repo_root, "branch", "--show-current") or "unknown"
    report["commit"] = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    report["errors"] = errors
    report["status"] = "ready" if not errors else "not_ready"
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S7 offline/intranet research citations contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S7 offline/intranet research citations: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
