#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kq_exec_memo_deck_generation import build_kq1b_capabilities_report  # noqa: E402

REQUIRED_FILES = (
    "backend/app/services/slides_service/kq_exec_memo_deck_generation.py",
    "backend/app/services/slides_service/kq_deck_quality.py",
    "scripts/kw_kq1b_exec_memo_pptx_check.py",
    "scripts/kw_kq1b_exec_memo_pptx_generate.py",
    "backend/tests/smoke/test_kq1b_exec_memo_deck_generation.py",
    "docs/codex/KQ1B_EXEC_MEMO_ACTUAL_PPTX_GENERATION.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KQ-1B executive memo actual PPTX generation capability.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    errors = [f"missing required file: {path}" for path in REQUIRED_FILES if not (repo_root / path).exists()]
    report = build_kq1b_capabilities_report()
    report.update(
        {
            "status": "ready" if not errors else "failed",
            "errors": errors,
            "required_files": list(REQUIRED_FILES),
        }
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
