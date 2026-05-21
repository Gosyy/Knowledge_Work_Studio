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

from backend.app.services.slides_service.native_visuals import native_visual_rendering_report  # noqa: E402

EXPECTED_BASE_AFTER_S3 = "c75656b23b5166a4b79ded85c1968ab74ee0185c"
REQUIRED_FILES = (
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S3_ADAPTIVE_DECK_MODES.md",
    "docs/codex/S4_NATIVE_TABLE_CHART_DIAGRAM_RENDERING.md",
    "backend/app/services/slides_service/adaptive_deck_modes.py",
    "backend/app/services/slides_service/native_visuals.py",
    "scripts/kw_s3_adaptive_deck_modes_check.py",
    "scripts/kw_s4_native_visual_rendering_check.py",
    "backend/tests/smoke/test_s4_native_visual_rendering.py",
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


def run_checker(repo_root: Path, script: str, require_ready: bool) -> tuple[dict[str, Any] | None, str]:
    command = [sys.executable, script, "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    payload = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S4 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S3:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S3, head)
            if ancestry is False:
                errors.append(f"expected S3 baseline {EXPECTED_BASE_AFTER_S3} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S3 ancestry for {EXPECTED_BASE_AFTER_S3}..{head}")
        s3_payload, s3_output = run_checker(repo_root, "scripts/kw_s3_adaptive_deck_modes_check.py", require_ready=True)
        if s3_payload is None:
            errors.append(f"could not parse S3 checker output before S4: {s3_output[:500]}")
        elif s3_payload.get("status") != "ready":
            errors.append(f"S3 checker is not ready before S4: {s3_payload.get('status')!r}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    report = native_visual_rendering_report()
    static_errors = collect_static_errors(repo_root, require_ready)
    if static_errors:
        report["errors"].extend(static_errors)
        report["status"] = "not_ready"
        report["native_table_chart_diagram_rendering_completed_by_s4"] = False
    report["repo_root"] = str(repo_root)
    report["branch"] = run_git(repo_root, "branch", "--show-current") or "unknown"
    report["commit"] = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    report["expected_base_after_s3"] = EXPECTED_BASE_AFTER_S3
    report["required_files"] = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio S4 native table/chart/diagram rendering contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = build_report(repo_root, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[s4-native-visual-rendering]")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
        if report["status"] == "ready":
            print("[PASS] S4 native table/chart/diagram rendering completed")
        else:
            for error in report.get("errors", []):
                print(f"[FAIL] {error}")
    return 0 if report["status"] == "ready" or not args.require_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
