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

from backend.app.services.slides_service.selected_benchmark_execution_packet import (  # noqa: E402
    selected_benchmark_execution_packet_report,
)

EXPECTED_BASE_AFTER_S11 = "29da8cdd030c9cd75ac1f62068f395a870d85c89"
REQUIRED_FILES = (
    "docs/codex/S10_EXPANDED_KIMI_STYLE_BENCHMARK.md",
    "docs/codex/S11_S_PHASE_CLOSURE_DOSSIER.md",
    "docs/codex/S12_SELECTED_BENCHMARK_EXECUTION_PACKET.md",
    "backend/app/services/slides_service/kimi_style_benchmark.py",
    "backend/app/services/slides_service/s_phase_closure.py",
    "backend/app/services/slides_service/selected_benchmark_execution_packet.py",
    "scripts/kw_s12_selected_benchmark_execution_packet_check.py",
    "backend/tests/smoke/test_s12_selected_benchmark_execution_packet.py",
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
    errors = [f"missing S12 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "9_Product_Release_Hardening":
            errors.append(f"expected branch 9_Product_Release_Hardening, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S11:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S11, head)
            if ancestry is False:
                errors.append(f"expected S11 baseline {EXPECTED_BASE_AFTER_S11} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S11 ancestry for {EXPECTED_BASE_AFTER_S11}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, object]:
    report = selected_benchmark_execution_packet_report()
    errors = list(report.get("errors", []))
    errors.extend(collect_static_errors(repo_root, require_ready))
    if errors:
        report = dict(report)
        report["status"] = "not_ready"
        report["errors"] = errors
    report["repo_root"] = str(repo_root)
    report["expected_base_after_s11"] = EXPECTED_BASE_AFTER_S11
    report["branch"] = run_git(repo_root, "branch", "--show-current") or "unknown"
    report["commit"] = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S12 selected benchmark execution packet and human review workflow.")
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
        print(f"S12 selected benchmark execution packet: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
