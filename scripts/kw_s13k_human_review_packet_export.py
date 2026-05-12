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

from backend.app.services.slides_service.s13j_human_review_packet import (  # noqa: E402
    build_human_review_packet_from_s13j,
    zip_packet,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export S13k human review packet from S13j merged 12/12 artifacts.")
    parser.add_argument("--s13j-live-input", type=Path, required=True, help="S13j live ZIP or extracted artifacts directory")
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.packet_dir.exists():
        shutil.rmtree(args.packet_dir)
    report = build_human_review_packet_from_s13j(args.s13j_live_input.resolve(), args.packet_dir.resolve())
    zip_packet(args.packet_dir.resolve(), args.zip_out.resolve())
    report["zip_out"] = str(args.zip_out.resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13k human review packet export: {report['status']}")
        print(f"zip: {args.zip_out}")
        for error in report.get("errors", []):
            print(f"- {error}")
    if args.require_ready and report.get("status") != "ready":
        return 1
    return 0 if report.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
