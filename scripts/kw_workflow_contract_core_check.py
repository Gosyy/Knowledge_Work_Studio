#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_repo_on_path(repo_root: Path) -> None:
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


def load_report(repo_root: Path) -> dict[str, Any]:
    ensure_repo_on_path(repo_root)
    from backend.app.workflows.core_contracts import workflow_contract_core_report

    return workflow_contract_core_report()


def filter_report(report: dict[str, Any], workflow_id: str | None) -> dict[str, Any]:
    if not workflow_id:
        return report
    contracts = report.get("contracts", {})
    if workflow_id not in contracts:
        filtered = dict(report)
        filtered["status"] = "not_ready"
        filtered["contracts"] = {}
        filtered["workflow_count"] = 0
        filtered["errors"] = list(report.get("errors", [])) + [f"unknown workflow contract core: {workflow_id}"]
        return filtered
    filtered = dict(report)
    filtered["contracts"] = {workflow_id: contracts[workflow_id]}
    filtered["workflow_count"] = 1
    return filtered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio KR-4A workflow contract core.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--workflow", default=None, help="Optional workflow id, for example xlsx or slides.")
    parser.add_argument("--json", action="store_true", help="Print only JSON output.")
    parser.add_argument("--require-ready", action="store_true", help="Fail if the workflow contract core has errors.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    report = filter_report(load_report(repo_root), args.workflow)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[workflow-contract-core]")
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["status"] == "ready":
            print("[PASS] workflow contract core completed")
        else:
            print("[FAIL] workflow contract core has errors")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
