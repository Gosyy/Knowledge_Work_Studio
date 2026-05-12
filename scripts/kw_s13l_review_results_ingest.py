#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.s13k_review_results_ingest import (  # noqa: E402
    build_s13l_ingest_report,
    zip_ingest_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest completed S13k human review results into an S13l decision/backlog artifact.")
    parser.add_argument("--review-results", type=Path, required=True, help="Completed S13k review results ZIP, directory, or JSON file")
    parser.add_argument("--s13k-packet", type=Path, required=True, help="Source S13k human review packet ZIP or extracted directory")
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.artifacts_dir.exists():
        shutil.rmtree(args.artifacts_dir)
    report = build_s13l_ingest_report(
        args.review_results,
        s13k_packet_input=args.s13k_packet,
        artifacts_dir=args.artifacts_dir,
    )
    zip_ingest_artifacts(args.artifacts_dir, args.zip_out)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13l review results ingest: {report['status']}")
        print(f"completed decisions: {report['completed_human_review_decision_count']}/{report['expected_review_worksheet_count']}")
        print(f"approve: {report['approve_count']}")
        print(f"request_rework: {report['request_rework_count']}")
        print(f"reject: {report['reject_count']}")
        print(f"release decision after S13l: {report['release_decision_after_s13l']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
