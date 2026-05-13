#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kq_pptx_render_qa import build_kq1c_capabilities_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KQ-1C independent PPTX render + visual QA capability.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-office-render-stack", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_kq1c_capabilities_report()
    payload["repo_root"] = str(args.repo_root)
    required_keys = (
        "independent_pptx_render_qa_supported",
        "kq1a_validation_after_independent_render_supported",
    )
    missing = [key for key in required_keys if payload.get(key) is not True]

    fallback_stack_available = payload.get("python_pptx_available") is True and payload.get("pillow_available") is True
    office_stack_available = payload.get("office_render_stack_available") is True
    if not office_stack_available and not fallback_stack_available:
        missing.append("office_render_stack_available_or_python_fallback_stack")

    if args.require_office_render_stack and not office_stack_available:
        missing.append("office_render_stack_available")
    payload["status"] = "ready" if not missing else "failed"
    payload["errors"] = [f"required capability not ready: {key}" for key in missing]
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.require_ready and payload["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
