#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kq_deck_quality import (  # noqa: E402
    assess_kq1a_deck_artifact_bundle,
    make_zip_from_dir,
    write_kq1a_assessment_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assess an executive_memo_to_board_deck artifact bundle with KQ-1A quality harness.")
    parser.add_argument("--bundle", type=Path, required=True, help="Deck artifact bundle ZIP or extracted directory.")
    parser.add_argument("--artifacts-dir", type=Path, required=True, help="Directory where KQ-1A report artifacts are written.")
    parser.add_argument("--zip-out", type=Path, help="Optional ZIP path for the generated KQ-1A assessment artifacts.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = assess_kq1a_deck_artifact_bundle(args.bundle)
    write_kq1a_assessment_artifacts(result, args.artifacts_dir)
    if args.zip_out:
        make_zip_from_dir(args.artifacts_dir, args.zip_out)
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] bundle={args.bundle}")
        print(f"[INFO] artifacts_dir={args.artifacts_dir}")
        if args.zip_out:
            print(f"[INFO] zip_out={args.zip_out}")
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result.status != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
