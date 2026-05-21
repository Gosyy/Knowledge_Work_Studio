#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kq_deck_quality import make_zip_from_dir  # noqa: E402
from backend.app.services.slides_service.kq_exec_memo_deck_generation import generate_kq1b_exec_memo_deck_bundle  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate KQ-1B executive_memo_to_board_deck PPTX artifact bundle.")
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Directory where the generated deck artifact bundle is written.")
    parser.add_argument("--zip-out", type=Path, help="Optional ZIP path for the generated bundle.")
    parser.add_argument("--quality-report-dir", type=Path, help="Directory where KQ-1A quality report artifacts are written.")
    parser.add_argument("--quality-report-zip", type=Path, help="Optional ZIP path for the KQ-1A quality report artifacts.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    quality_dir = args.quality_report_dir or (args.bundle_dir / "kq1a_quality_report")
    result = generate_kq1b_exec_memo_deck_bundle(args.bundle_dir, zip_out=args.zip_out, quality_report_dir=quality_dir)
    if args.quality_report_zip:
        make_zip_from_dir(quality_dir, args.quality_report_zip)
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result.status != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
