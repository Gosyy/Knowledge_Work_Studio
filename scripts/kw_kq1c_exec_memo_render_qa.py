#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kq_pptx_render_qa import run_kq1c_independent_render_qa  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run KQ-1C independent PPTX render + visual QA over an executive memo deck bundle.")
    parser.add_argument("--input-bundle", type=Path, required=True, help="KQ-1B deck artifact bundle ZIP or extracted bundle directory.")
    parser.add_argument("--output-bundle-dir", type=Path, required=True, help="Directory where the KQ-1C enhanced bundle is written.")
    parser.add_argument("--zip-out", type=Path, help="Optional ZIP path for the KQ-1C enhanced bundle.")
    parser.add_argument("--quality-report-dir", type=Path, help="Directory for KQ-1A quality report after KQ-1C.")
    parser.add_argument("--quality-report-zip", type=Path, help="Optional ZIP path for KQ-1A quality report after KQ-1C.")
    parser.add_argument("--render-mode", choices=("auto", "libreoffice", "python-pptx-text"), default="auto")
    parser.add_argument("--require-office-render", action="store_true", help="Fail unless LibreOffice/PDF render was actually used.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_kq1c_independent_render_qa(
        args.input_bundle,
        args.output_bundle_dir,
        zip_out=args.zip_out,
        quality_report_dir=args.quality_report_dir,
        quality_report_zip=args.quality_report_zip,
        render_mode=args.render_mode,
        require_office_render=args.require_office_render,
    )
    payload = result.as_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result.status != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
