#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.app.services.slides_service.plan_first_contract import (
    RENDER_MODES,
    slides_plan_first_report,
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def required_paths(repo_root: Path) -> tuple[str, ...]:
    return (
        "backend/app/services/slides_service/plan_first_contract.py",
        "backend/app/workflows/contracts.py",
        "docs/workflow-contracts.md",
        "docs/slides-plan-first-ux.md",
    )


def validate_required_paths(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in required_paths(repo_root):
        if not (repo_root / rel).exists():
            errors.append(f"missing required path: {rel}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate KW Studio slides plan-first UX contract without network calls."
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--mode", choices=("all", *RENDER_MODES), default="all", help="Render mode to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--require-ready", action="store_true", help="Fail when the contract is not ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    mode = None if args.mode == "all" else args.mode
    report = slides_plan_first_report(mode=mode)
    errors = validate_required_paths(repo_root)
    if errors:
        report["errors"].extend(errors)
        report["status"] = "not_ready"
    report["repo_root"] = str(repo_root)
    report["required_paths"] = {rel: (repo_root / rel).exists() for rel in required_paths(repo_root)}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[slides-plan-first]")
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["status"] == "ready":
            print("[PASS] slides plan-first UX contract completed")
        else:
            for error in report["errors"]:
                print(f"[FAIL] {error}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
