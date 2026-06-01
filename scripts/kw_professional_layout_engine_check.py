#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "backend/app/services/slides_service/professional_layout_engine.py",
    "backend/tests/services/test_kr7l_professional_layout_engine.py",
    "scripts/kw_professional_layout_engine_check.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)

REQUIRED_DOC_PHRASES = (
    "presentation_professional_layout_engine.v1",
    "KR-7L professional layout engine",
    "no_renderer_runtime_mapping",
    "no_production_layout_quality_claim",
)


def _git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_report(repo_root: Path) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(repo_root))
    from backend.app.services.slides_service import (  # noqa: WPS433
        PROFESSIONAL_LAYOUT_SCHEMA_VERSION,
        ProfessionalLayoutSlideRequest,
        sample_professional_layout_report,
        solve_professional_layout,
    )
    from backend.app.services.slides_service.template_brand_profile import sample_template_brand_profile_report  # noqa: WPS433

    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing KR-7L required file: {rel}")

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
                errors.append(f"{rel} missing KR-7L phrase: {phrase}")

    report = sample_professional_layout_report()
    if report.get("schema_version") != PROFESSIONAL_LAYOUT_SCHEMA_VERSION:
        errors.append("sample professional layout report schema version mismatch")
    if report.get("status") not in {"ready", "degraded"}:
        errors.append("sample professional layout report must be ready or degraded, not blocked")
    if report.get("professional_layout_engine_implemented") is not True:
        errors.append("KR-7L must implement deterministic layout engine contract")
    for field in (
        "deterministic_layout_solver_implemented",
        "grid_layout_implemented",
        "typographic_scale_implemented",
        "text_fitting_implemented",
        "overlap_detection_implemented",
        "contrast_density_readability_scores_implemented",
        "title_clipping_prevention_implemented",
    ):
        if report.get(field) is not True:
            errors.append(f"KR-7L report missing true flag: {field}")

    if report.get("native_pptx_layout_mapping_implemented") is not False:
        errors.append("KR-7L must not claim native PPTX layout mapping")
    if report.get("renderer_runtime_changed") is not False:
        errors.append("KR-7L must not change renderer runtime")
    if report.get("rendered_png_qa_executed") is not False:
        errors.append("KR-7L must not claim rendered PNG QA execution")
    if report.get("visual_qa_executed") is not False:
        errors.append("KR-7L must not execute visual QA")
    if report.get("production_layout_claimed") is not False:
        errors.append("KR-7L must not claim production layout quality")
    if report.get("kimi_level_quality_claimed") is not False:
        errors.append("KR-7L must not claim Kimi-level quality")

    for slide in report.get("slide_plans", []):
        if slide.get("overlap_count") != 0:
            errors.append(f"sample slide has overlapping blocks: {slide.get('slide_id')}")
        if slide.get("title_clipped") is not False:
            errors.append(f"sample slide has clipped title: {slide.get('slide_id')}")
        for score in ("density_score", "contrast_score", "readability_score", "layout_score"):
            value = slide.get(score)
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                errors.append(f"sample slide has invalid {score}: {slide.get('slide_id')}")

    blocked = solve_professional_layout(
        [ProfessionalLayoutSlideRequest(slide_id="s_bad", role="content", title=" ".join(["LongTitleToken"] * 120))],
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()
    if blocked.get("status") != "blocked" or blocked.get("slide_plans", [{}])[0].get("title_clipped") is not True:
        errors.append("KR-7L must fail closed when a title cannot fit minimum font")

    payload = dict(report)
    payload.update(
        {
            "checker_schema_version": "kw_professional_layout_engine_check.v1",
            "status": "ready" if not errors else "blocked",
            "branch": _git(repo_root, "branch", "--show-current") or "unknown",
            "commit": _git(repo_root, "rev-parse", "HEAD") or "unknown",
            "required_paths": {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES},
            "previous_phase": "KR-7K data-backed charts",
            "next_phase": "KR-7M Presentation Studio UI",
            "errors": errors,
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-7L professional layout engine contract.")
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
