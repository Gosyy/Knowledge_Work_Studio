#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_repo(repo_root: Path) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(repo_root))
    from backend.app.services.slides_service import (  # noqa: WPS433
        SOURCE_IMAGE_SELECTION_SCHEMA_VERSION,
        SourceImageSlideRequest,
        sample_source_image_selection_report,
        select_source_images_for_slides,
    )
    from backend.app.services.slides_service.source_asset_registry import StoredSourceAsset  # noqa: WPS433
    from backend.app.services.slides_service.template_brand_profile import sample_template_brand_profile_report  # noqa: WPS433

    source_asset = StoredSourceAsset(
        registry_entry_id="registry_market_chart_image",
        asset_id="market_chart_image",
        source_id="uploaded_market_report",
        asset_type="image",
        source_package_path="ppt/media/market_chart.png",
        relative_path="uploaded_market_report/assets/market_chart_image.png",
        storage_uri="source-asset://uploaded_market_report/market_chart_image",
        provenance_ref="uploaded_market_report#slide:2#image:market_chart",
        checksum_sha256="a" * 64,
        size_bytes=128000,
        mime_type="image/png",
        slide_number=2,
        width_px=1280,
        height_px=720,
    )
    selected = select_source_images_for_slides(
        [
            SourceImageSlideRequest(
                slide_id="s001",
                role="data",
                title="Market chart evidence",
                intent_query="market chart revenue evidence",
                expected_terms=("market", "chart", "revenue"),
                requires_image=True,
            ),
            SourceImageSlideRequest(
                slide_id="s002",
                role="roadmap",
                title="Roadmap",
                intent_query="roadmap milestones",
                expected_terms=("roadmap", "milestones"),
                requires_image=True,
            ),
            SourceImageSlideRequest(
                slide_id="s003",
                role="cover",
                title="Template media brand",
                intent_query="template media brand",
                expected_terms=("template", "media"),
            ),
        ],
        source_assets=[source_asset],
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()
    sample = sample_source_image_selection_report()
    return {
        "schema_version": "kw_source_image_selection_check.v1",
        "status": "ready",
        "selection_schema_version": SOURCE_IMAGE_SELECTION_SCHEMA_VERSION,
        "sample": sample,
        "selection": selected,
        "problems": [],
    }


def _validate(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    selection = report.get("selection") or {}
    sample = report.get("sample") or {}
    for payload_name, payload in (("sample", sample), ("selection", selection)):
        if payload.get("schema_version") != report["selection_schema_version"]:
            problems.append(f"{payload_name} schema version mismatch")
        if payload.get("source_image_selection_implemented") is not True:
            problems.append(f"{payload_name} source image selection not implemented")
        if payload.get("source_images_only_enforced") is not True:
            problems.append(f"{payload_name} source image only guardrail missing")
        if payload.get("generated_images_allowed") is not False:
            problems.append(f"{payload_name} generated images must not be allowed")
        if payload.get("random_images_allowed") is not False:
            problems.append(f"{payload_name} random images must not be allowed")
        if payload.get("fake_artifacts_allowed") is not False:
            problems.append(f"{payload_name} fake artifacts must not be allowed")
        if payload.get("inline_image_payloads_allowed") is not False:
            problems.append(f"{payload_name} inline image payloads must not be allowed")
        if payload.get("renderer_runtime_changed") is not False:
            problems.append(f"{payload_name} renderer runtime must remain unchanged")
        if payload.get("visual_qa_executed") is not False:
            problems.append(f"{payload_name} visual QA must stay out of KR-7J")
        if payload.get("kimi_level_quality_claimed") is not False:
            problems.append(f"{payload_name} Kimi-level quality must not be claimed")
    selected_bindings = [binding for binding in selection.get("slide_bindings", []) if binding.get("status") == "selected"]
    if len(selected_bindings) < 2:
        problems.append("expected at least two deterministic selected bindings from document/template source assets")
    for binding in selected_bindings:
        if not binding.get("citation") or not binding.get("provenance_ref"):
            problems.append(f"selected binding {binding.get('slide_id')} lacks citation/provenance")
    fallback_bindings = [binding for binding in selection.get("slide_bindings", []) if binding.get("status") == "typographic_fallback"]
    if not fallback_bindings:
        problems.append("expected typographic fallback when no relevant source image exists")
    if any(candidate.get("source_kind") not in {"uploaded_document", "uploaded_template"} for candidate in selection.get("candidates", [])):
        problems.append("candidate source kind must be uploaded_document or uploaded_template only")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KR-7J source image selection contract.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = _load_repo(repo_root)
    problems = _validate(report)
    if problems:
        report["status"] = "blocked"
        report["problems"] = problems
    print(f"kw_source_image_selection_check.py: {report['status']}")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
