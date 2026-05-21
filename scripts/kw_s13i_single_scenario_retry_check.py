#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.single_scenario_s13h_retry import single_scenario_executive_memo_retry_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13i single-scenario executive memo retry contract.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = single_scenario_executive_memo_retry_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13i single-scenario executive memo retry: {report['status']}")
        print(f"retry_scenario_ids={report.get('retry_scenario_ids')}")
        print(f"reused_canonical_scenario_count={report.get('reused_canonical_scenario_count')}")
        for error in report.get("errors", []):
            print(f"- {error}")
    if args.require_ready and report.get("status") != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
