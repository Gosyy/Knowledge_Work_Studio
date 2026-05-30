#!/usr/bin/env python3
"""KR-7I template and brand understanding checker."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service import (  # noqa: E402
    TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION,
    sample_template_brand_profile_report,
    validate_template_reference,
)

REQUIRED_FILES = (
    "backend/app/services/slides_service/template_brand_profile.py",
    "backend/tests/services/test_kr7i_template_brand_profile.py",
    "scripts/kw_template_brand_profile_check.py",
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)

REQUIRED_DOC_PHRASES = (
    "presentation_template_brand_profile.v1",
    "KR-7I template and brand understanding",
    "no_template_clone_rewrite_mode",
    "no_production_layout_engine",
)


def _git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_report(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing KR-7I required file: {rel}")

    for rel in (
        "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
        "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
        "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
    ):
        path = repo_root / rel
        text = _read(path) if path.exists() else ""
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in text:
                errors.append(f"{rel} missing KR-7I phrase: {phrase}")

    report = sample_template_brand_profile_report()
    if report.get("schema_version") != TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION:
        errors.append("sample report schema version mismatch")
    if report.get("status") != "ready":
        errors.append("sample template brand profile report is not ready")
    if report.get("template_content_copied") is not False:
        errors.append("KR-7I profile must not copy old template content")
    if report.get("production_layout_engine_implemented") is not False:
        errors.append("KR-7I profile must not claim production layout engine")
    if report.get("renderer_runtime_changed") is not False:
        errors.append("KR-7I profile must not change renderer runtime")
    if report.get("visual_qa_executed") is not False:
        errors.append("KR-7I profile must not execute visual QA")
    if report.get("kimi_level_quality_claimed") is not False:
        errors.append("KR-7I profile must not claim Kimi-level quality")
    if not report.get("slide_size"):
        errors.append("KR-7I profile must parse slide size")
    theme = report.get("theme") or {}
    if not theme.get("color_tokens") or not theme.get("major_font") or not theme.get("minor_font"):
        errors.append("KR-7I profile must parse theme colors and fonts")
    if int(report.get("slide_masters_count") or 0) < 1:
        errors.append("KR-7I profile must detect slide masters")
    if int(report.get("slide_layout_count") or 0) < 3:
        errors.append("KR-7I profile must detect multiple layouts")
    if int(report.get("media_asset_count") or 0) < 1:
        errors.append("KR-7I profile must detect template media assets")
    if not validate_template_reference("https://example.com/template.pptx"):
        errors.append("KR-7I must reject external template references")

    payload = dict(report)
    payload.update(
        {
            "checker_schema_version": "kw_template_brand_profile_check.v1",
            "status": "ready" if not errors else "blocked",
            "branch": _git(repo_root, "branch", "--show-current") or "unknown",
            "commit": _git(repo_root, "rev-parse", "HEAD") or "unknown",
            "required_paths": {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES},
            "kr7h_closed_required": True,
            "previous_phase": "KR-7H.13 renderer worker closure gate",
            "next_phase": "KR-7J source image selection",
            "errors": errors,
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-7I template and brand profile contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_report(args.repo_root.resolve())
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and payload.get("status") != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
