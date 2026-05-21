#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.s13k_review_results_ingest import s13l_review_results_ingest_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check S13l completed S13k review results ingest contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = s13l_review_results_ingest_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={args.repo_root.resolve()}")
        print("[s13l-completed-s13k-review-results-ingest]")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        if not args.json:
            for error in report["errors"]:
                print(f"[FAIL] {error}")
        return 1
    if not args.json:
        print("[PASS] S13l completed review results ingest contract ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
