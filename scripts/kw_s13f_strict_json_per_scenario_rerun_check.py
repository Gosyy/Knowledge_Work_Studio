#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.app.services.slides_service.strict_json_per_scenario_rerun import strict_json_per_scenario_rerun_report

def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13f strict per-scenario JSON rerun contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = strict_json_per_scenario_rerun_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13f strict per-scenario JSON rerun: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 1 if args.require_ready and report.get("status") != "ready" else 0

if __name__ == "__main__":
    raise SystemExit(main())
