#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio S8 browser-assisted internal evidence capture contract.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root path.")
    parser.add_argument("--mode", choices=("capture", "slides_link"), default="capture", help="Evidence contract mode to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--require-ready", action="store_true", help="Fail unless contract status is ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    from backend.app.workflows.browser_evidence_capture_contract import build_browser_evidence_report

    report = build_browser_evidence_report(args.mode)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[browser-evidence-capture]")
        print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_ready and report["status"] != "ready":
        for error in report["errors"]:
            print(f"[FAIL] {error}")
        return 2

    if not args.json:
        print("[PASS] browser evidence capture contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
