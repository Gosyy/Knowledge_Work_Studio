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

from backend.app.services.slides_service.live_benchmark_prompt_schema_hardening import live_benchmark_prompt_schema_hardening_report  # noqa: E402

EXPECTED_ANCESTOR = "8517ff7565bc13043da560e2aafe5130c7f49eb2"


def _git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13d live benchmark prompt/schema hardening contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = live_benchmark_prompt_schema_hardening_report()
    errors = list(report.get("errors", []))
    if args.require_ready:
        branch = _git(repo_root, "branch", "--show-current")
        if branch != "9_Product_Release_Hardening":
            errors.append(f"expected branch 9_Product_Release_Hardening, got {branch}")
        head = _git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_ANCESTOR:
            ancestry = _is_ancestor(repo_root, EXPECTED_ANCESTOR, head)
            if ancestry is False:
                errors.append(f"expected S13c verdict {EXPECTED_ANCESTOR} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append("could not verify S13c ancestry")
    payload = dict(report)
    payload["errors"] = errors
    payload["status"] = "ready" if not errors else "not_ready"
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13d live benchmark prompt/schema hardening: {payload['status']}")
        print(f"hardened_prompt_policy_count={payload.get('hardened_prompt_policy_count')}")
        print(f"minimum_slide_count_per_scenario={payload.get('minimum_slide_count_per_scenario_by_s13d')}")
        for error in errors:
            print(f"- {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
