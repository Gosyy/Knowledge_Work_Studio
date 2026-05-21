#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.s13j_human_review_packet import (  # noqa: E402
    s13k_human_review_packet_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check S13k human review packet export contract from S13j merged artifacts.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = s13k_human_review_packet_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={args.repo_root.resolve()}")
        print("[s13k-human-review-packet-from-s13j]")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        if not args.json:
            for error in report["errors"]:
                print(f"[FAIL] {error}")
        return 1
    if not args.json:
        print("[PASS] S13k human review packet export contract ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
