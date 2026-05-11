#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.render_based_visual_qa import render_based_visual_qa_report

EXPECTED_BASE_AFTER_S8 = "79e4e71463f2a68668c039f2e9f35d6faabe7f52"
REQUIRED_FILES = (
    "backend/app/services/slides_service/render_based_visual_qa.py",
    "backend/app/services/slides_service/adaptive_deck_modes.py",
    "backend/app/services/slides_service/native_visuals.py",
    "backend/app/services/slides_service/image_to_slide_workflow.py",
    "backend/app/services/slides_service/offline_research_citations.py",
    "backend/app/services/slides_service/conversational_edit_loop.py",
    "docs/codex/S9_RENDER_BASED_VISUAL_QA.md",
    "scripts/kw_s9_render_based_visual_qa_check.py",
    "backend/tests/smoke/test_s9_render_based_visual_qa.py",
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


def validate_required_paths(repo_root: Path) -> list[str]:
    return [f"missing S9 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]


def validate_git(repo_root: Path, require_ready: bool) -> list[str]:
    if not require_ready:
        return []
    errors: list[str] = []
    branch = run_git(repo_root, "branch", "--show-current")
    if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
        errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
    head = run_git(repo_root, "rev-parse", "HEAD")
    if head and head != EXPECTED_BASE_AFTER_S8:
        ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S8, head)
        if ancestry is False:
            errors.append(f"expected S8 baseline {EXPECTED_BASE_AFTER_S8} to be an ancestor of HEAD {head}")
        elif ancestry is None:
            errors.append(f"could not verify S8 ancestry for {EXPECTED_BASE_AFTER_S8}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, object]:
    report = render_based_visual_qa_report()
    errors = list(report.get("errors", []))
    errors.extend(validate_required_paths(repo_root))
    errors.extend(validate_git(repo_root, require_ready))
    report["repo_root"] = str(repo_root)
    report["required_paths"] = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    report["expected_base_after_s8"] = EXPECTED_BASE_AFTER_S8
    report["branch"] = run_git(repo_root, "branch", "--show-current") or "unknown"
    report["commit"] = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    report["errors"] = errors
    report["status"] = "ready" if not errors else "not_ready"
    report["render_based_visual_qa_completed_by_s9"] = not errors
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S9 render-based visual QA contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S9 render-based visual QA: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
