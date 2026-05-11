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

from backend.app.services.slides_service.kimi_style_benchmark import kimi_style_benchmark_report  # noqa: E402

EXPECTED_BASE_AFTER_S9 = "e2954d5e9d837571567c14b184cbc5dcebe86a7f"
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S10_EXPANDED_KIMI_STYLE_BENCHMARK.md",
    "backend/app/services/slides_service/kimi_style_benchmark.py",
    "scripts/kw_s10_kimi_style_benchmark_check.py",
    "backend/tests/smoke/test_s10_kimi_style_benchmark.py",
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
    errors = [f"missing S10 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S9:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S9, head)
            if ancestry is False:
                errors.append(f"expected S9 baseline {EXPECTED_BASE_AFTER_S9} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S9 ancestry for {EXPECTED_BASE_AFTER_S9}..{head}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio S10 expanded Kimi-style benchmark and human review contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = kimi_style_benchmark_report()
    report["repo_root"] = str(repo_root)
    report["expected_base_after_s9"] = EXPECTED_BASE_AFTER_S9
    static_errors = collect_static_errors(repo_root, args.require_ready)
    if static_errors:
        report["errors"].extend(static_errors)
        report["status"] = "not_ready"
        report["expanded_kimi_style_benchmark_completed_by_s10"] = False

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S10 expanded Kimi-style benchmark: {report['status']}")
        print(f"scenario count: {report['scenario_count']}")
        print(f"accepted claim wording: {report['accepted_final_claim_wording_by_s10']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
