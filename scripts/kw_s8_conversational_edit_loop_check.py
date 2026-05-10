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

from backend.app.services.slides_service.conversational_edit_loop import conversational_edit_loop_report  # noqa: E402

EXPECTED_BASE_AFTER_S7 = "16887ec2c764f5bc149802357682ae381e7885fe"
REQUIRED_FILES = (
    "docs/codex/S7_OFFLINE_INTRANET_RESEARCH_CITATIONS.md",
    "backend/app/services/slides_service/offline_research_citations.py",
    "scripts/kw_s7_offline_research_citations_check.py",
    "docs/codex/S8_CONVERSATIONAL_EDIT_LOOP.md",
    "backend/app/services/slides_service/conversational_edit_loop.py",
    "scripts/kw_s8_conversational_edit_loop_check.py",
    "backend/tests/smoke/test_s8_conversational_edit_loop.py",
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


def run_s7_checker(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_s7_offline_research_citations_check.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S8 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S7:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S7, head)
            if ancestry is False:
                errors.append(f"expected S7 baseline {EXPECTED_BASE_AFTER_S7} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S7 ancestry for {EXPECTED_BASE_AFTER_S7}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    report = conversational_edit_loop_report()
    errors = list(report.get("errors", []))
    errors.extend(collect_static_errors(repo_root, require_ready))
    s7_payload: dict[str, Any] | None = None
    if not errors:
        s7_payload, stdout, stderr, returncode = run_s7_checker(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"S7 checker failed during S8 validation with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        elif s7_payload is None:
            errors.append("S8 could not parse S7 checker JSON output")
        elif s7_payload.get("status") != "ready":
            errors.append(f"S7 checker status must be ready during S8 validation, got {s7_payload.get('status')!r}")
    payload = dict(report)
    payload.update({
        "status": "ready" if not errors else "not_ready",
        "repo_root": str(repo_root),
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_s7": EXPECTED_BASE_AFTER_S7,
        "s7_checker_status": s7_payload.get("status") if isinstance(s7_payload, dict) else None,
        "required_files": {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES},
        "errors": errors,
    })
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio S8 conversational edit loop contract.")
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
        print(f"S8 conversational edit loop: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
