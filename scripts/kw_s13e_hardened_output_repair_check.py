#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.hardened_output_repair import hardened_output_repair_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13e hardened output repair/parser contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = hardened_output_repair_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13e hardened output repair/parser: {report['status']}")
        print(f"scenario_count={report['scenario_count']}")
        print(f"deterministic_repair_only={report['deterministic_repair_only_by_s13e']}")
        print(f"live_gigachat_call_allowed={report['live_gigachat_call_allowed_by_s13e']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" or not args.require_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
