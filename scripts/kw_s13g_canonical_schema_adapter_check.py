#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.canonical_schema_adapter import canonical_schema_adapter_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S13g canonical schema adapter contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = canonical_schema_adapter_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13g canonical schema adapter: {report['status']}")
        print(f"scenario_count={report['scenario_count']}")
        print(f"minimal_prompt_required_by_s13g={report['minimal_prompt_required_by_s13g']}")
        print(f"canonical_adapter_required_by_s13g={report['canonical_adapter_required_by_s13g']}")
        print(f"adapter_provenance_required_by_s13g={report['adapter_provenance_required_by_s13g']}")
        print(f"selected_offline_workflow_parity_claim_supported_now_by_s13g={report['selected_offline_workflow_parity_claim_supported_now_by_s13g']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
