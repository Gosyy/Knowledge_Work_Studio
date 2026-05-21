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

from backend.app.services.slides_service.s_phase_closure import s_phase_closure_report

EXPECTED_BASE_AFTER_S10 = "c2ad133c54b872b8af69e1611464e9466016cbec"
REQUIRED_FILES = (
    "docs/codex/S11_S_PHASE_CLOSURE_DOSSIER.md",
    "backend/app/services/slides_service/s_phase_closure.py",
    "scripts/kw_s11_s_phase_closure_check.py",
    "backend/tests/smoke/test_s11_s_phase_closure.py",
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


def validate_repo(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S11 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S10:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S10, head)
            if ancestry is False:
                errors.append(f"expected S10 baseline {EXPECTED_BASE_AFTER_S10} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S10 ancestry for {EXPECTED_BASE_AFTER_S10}..{head}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S11 S-phase closure dossier.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = s_phase_closure_report()
    errors = validate_repo(repo_root, args.require_ready)
    if errors:
        report = dict(report)
        report["errors"] = list(report.get("errors", [])) + errors
        report["status"] = "not_ready"
        report["s_phase_closure_completed_by_s11"] = False
    report["repo_root"] = str(repo_root)
    report["required_paths"] = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S11 S-phase closure dossier: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
