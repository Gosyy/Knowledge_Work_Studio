#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/S13C_LIVE_GIGACHAT_EVIDENCE_PACKET_EXPORT.md",
    "backend/app/services/slides_service/live_gigachat_evidence_packet.py",
    "scripts/kw_s13c_live_gigachat_evidence_packet_check.py",
    "scripts/kw_s13c_live_gigachat_evidence_packet_export.py",
    "backend/tests/smoke/test_s13c_live_gigachat_evidence_packet.py",
)
EXPECTED_ANCESTOR = "48a48f074a7862ecc266ebc596ab86ac505efead"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S13c required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "9_Product_Release_Hardening":
            errors.append(f"expected branch 9_Product_Release_Hardening, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_ANCESTOR, head)
            if ancestry is False:
                errors.append(f"expected S13b verdict {EXPECTED_ANCESTOR} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S13b ancestry for {EXPECTED_ANCESTOR}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    sys.path.insert(0, str(repo_root))
    try:
        from backend.app.services.slides_service.live_gigachat_evidence_packet import live_gigachat_evidence_packet_export_report
        report = live_gigachat_evidence_packet_export_report()
    except Exception as exc:
        report = {"status": "not_ready", "errors": [f"S13c import/report failed: {type(exc).__name__}: {exc}"]}
    if report.get("status") != "ready":
        errors.extend(str(err) for err in report.get("errors", []))
    return {
        "status": "ready" if not errors else "not_ready",
        "checkpoint": "S13c",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "s13c_report": report,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13c live GigaChat evidence packet export contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13c live GigaChat evidence packet export: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
