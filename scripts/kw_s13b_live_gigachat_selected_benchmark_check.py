#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.live_gigachat_selected_benchmark import (  # noqa: E402
    live_gigachat_selected_benchmark_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S13b live public_api_dev GigaChat selected benchmark generation contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = live_gigachat_selected_benchmark_report(dict(os.environ))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={args.repo_root.resolve()}")
        print("[s13b-live-public-api-dev-gigachat-generation]")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report.get("status") != "ready":
        return 1
    if not args.json:
        print("[PASS] S13b live public_api_dev GigaChat generation contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
