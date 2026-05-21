#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.render_mode_contract import (  # noqa: E402
    RENDER_MODES,
    slides_render_mode_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate KW Studio slides adaptive/template render mode contract.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root path.")
    parser.add_argument("--mode", choices=RENDER_MODES, default="adaptive", help="Render mode to validate.")
    parser.add_argument("--template-id", default=None, help="Local template id for template mode checks.")
    parser.add_argument(
        "--plan-snapshot-id",
        default="plansnap_contract",
        help="Plan snapshot id used for request validation.",
    )
    parser.add_argument("--approved-plan", action="store_true", default=True, help="Validate as if plan is approved.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--require-ready", action="store_true", help="Fail unless contract status is ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = slides_render_mode_report(
        mode=args.mode,
        template_id=args.template_id,
        plan_snapshot_id=args.plan_snapshot_id,
        approved_plan=args.approved_plan,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[slides-render-modes]")
        print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_ready and report["status"] != "ready":
        if not args.json:
            for error in report["errors"]:
                print(f"[FAIL] {error}")
        return 1

    if not args.json:
        print("[PASS] slides render mode contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
