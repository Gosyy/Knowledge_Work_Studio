#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.provenance_manifest_contract import (  # noqa: E402
    slides_provenance_manifest_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate KW Studio slides source-to-artifact provenance manifest contract.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root path.")
    parser.add_argument(
        "--mode",
        choices=("contract", "generation", "retry"),
        default="generation",
        help="Which provenance manifest slice to validate.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    parser.add_argument("--require-ready", action="store_true", help="Fail unless status is ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = slides_provenance_manifest_report(mode=args.mode)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[slides-provenance-manifest]")
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["status"] == "ready":
            print("[PASS] slides provenance manifest contract completed")
        else:
            for error in report["errors"]:
                print(f"[FAIL] {error}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
