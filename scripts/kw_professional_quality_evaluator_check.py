#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "presentation_professional_quality_evaluator.v1"
CHECKER_SCHEMA_VERSION = "kw_professional_quality_evaluator_check.v1"

REQUIRED_FILES = (
    "backend/app/services/slides_service/professional_quality_evaluator.py",
    "backend/tests/services/test_kr7n_professional_quality_evaluator.py",
    "scripts/kw_professional_quality_evaluator_check.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)

REQUIRED_DOC_PHRASES = (
    "presentation_professional_quality_evaluator.v1",
    "KR-7N professional quality evaluator",
    "quality_report.json",
    "no_visual_qa_runtime_execution",
    "no_kimi_level_quality_claim",
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
        PROFESSIONAL_QUALITY_SCHEMA_VERSION,
        evaluate_professional_quality,
        sample_professional_quality_report,
    )
    from backend.app.services.slides_service.professional_layout_engine import sample_professional_layout_report  # noqa: WPS433
    from backend.app.services.slides_service.professional_quality_evaluator import sample_export_proof_bundle_report  # noqa: WPS433
    from backend.app.services.slides_service.data_backed_charts import sample_data_backed_chart_report  # noqa: WPS433
    from backend.app.services.slides_service.source_image_selection import sample_source_image_selection_report  # noqa: WPS433

    errors: list[str] = []
    required_paths = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    for rel, exists in required_paths.items():
        if not exists:
            errors.append(f"missing KR-7N required file: {rel}")

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
                errors.append(f"{rel} missing KR-7N phrase: {phrase}")

    report = sample_professional_quality_report()
    if report.get("schema_version") != PROFESSIONAL_QUALITY_SCHEMA_VERSION or report.get("schema_version") != SCHEMA_VERSION:
        errors.append("professional quality report schema version mismatch")
    if report.get("status") != "ready":
        errors.append("sample professional quality report must be ready")
    if report.get("quality_pass") is not True:
        errors.append("sample professional quality report must pass quality gate")
    if report.get("overall_score", 0) < report.get("pass_threshold", 1):
        errors.append("overall professional quality score must meet pass threshold")
    if {axis.get("axis") for axis in report.get("axis_scores", [])} != {"content", "design", "coherence", "data", "assets", "export"}:
        errors.append("quality report must include all six professional quality axes")
    for field in (
        "content_quality_evaluated",
        "design_quality_evaluated",
        "coherence_quality_evaluated",
        "data_quality_evaluated",
        "asset_quality_evaluated",
        "export_quality_evaluated",
        "score_deterministic",
        "quality_report_schema_written",
        "kimi_level_professional_status_requires_quality_pass",
        "degraded_decks_marked_degraded",
    ):
        if report.get(field) is not True:
            errors.append(f"KR-7N report missing true flag: {field}")
    for field in (
        "visual_qa_runtime_executed",
        "rendered_png_qa_executed",
        "renderer_runtime_changed",
        "frontend_runtime_changed",
        "gigachat_runtime_changed",
        "docker_deploy_postgres_changed",
        "production_quality_claimed",
        "kimi_level_quality_claimed",
    ):
        if report.get(field) is not False:
            errors.append(f"KR-7N must not claim or change forbidden surface: {field}")

    blocked = evaluate_professional_quality(
        deck_title="Missing export proof",
        objective="Quality gate must fail closed when export proof is missing.",
        slide_titles=("Missing export proof",),
        slide_roles=("title",),
        evidence_refs=("evidence:proof",),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=sample_source_image_selection_report(),
        export_proof_bundle=None,
    ).as_dict()
    if blocked.get("status") != "blocked" or "export_missing_pdf_png_proof_bundle" not in blocked.get("blockers", []):
        errors.append("KR-7N must block decks without verified PDF/PNG export proof")

    degraded_image_report = sample_source_image_selection_report()
    degraded_image_report["slide_bindings"] = [{"slide_id": "s_typographic", "status": "typographic_fallback"}]
    degraded = evaluate_professional_quality(
        deck_title="Typographic fallback",
        objective="Quality gate must mark typographic fallback decks degraded, not fake success.",
        slide_titles=("Typographic fallback", "Asset gap"),
        slide_roles=("title", "insight"),
        evidence_refs=("evidence:asset-gap",),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=degraded_image_report,
        export_proof_bundle=sample_export_proof_bundle_report(),
    ).as_dict()
    if degraded.get("status") != "degraded" or degraded.get("degraded_deck") is not True:
        errors.append("KR-7N must mark degraded decks as degraded")

    full_runner_text = _read(repo_root / "scripts/kw_full_tests_with_proxy_runner.sh")
    if "29n-professional-quality-evaluator-check" not in full_runner_text:
        errors.append("full runner must include KR-7N professional quality evaluator check step")
    inventory_text = _read(repo_root / "scripts/kw_test_inventory.py")
    if "kw_professional_quality_evaluator_check" not in inventory_text:
        errors.append("test inventory must classify KR-7N professional quality evaluator checker")

    payload = dict(report)
    payload.update(
        {
            "checker_schema_version": CHECKER_SCHEMA_VERSION,
            "status": "ready" if not errors else "blocked",
            "previous_phase": "KR-7M Presentation Studio UI",
            "next_phase": "KR-7O scenario packs",
            "branch": _git(repo_root, "branch", "--show-current") or "unknown",
            "commit": _git(repo_root, "rev-parse", "HEAD") or "unknown",
            "required_paths": required_paths,
            "errors": errors,
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-7N professional quality evaluator contract.")
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
