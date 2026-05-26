from __future__ import annotations

from backend.app.services.slides_service import (
    PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
    PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
    PRESENTATION_IR_SCHEMA_VERSION,
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    require_presentation_ir_payload,
)


def _evidence_index():
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_planner",
        file_type="md",
    )
    return OfflineEvidenceIndexBuilder().build_index([report])


def test_kr7f1_planner_builds_valid_presentation_ir_from_offline_evidence() -> None:
    index = _evidence_index()
    request = PresentationIRPlannerRequest(
        presentation_id="pres_kr7f",
        title="Support automation results",
        objective="Show source-backed impact of support automation",
        slide_count=5,
        require_evidence=True,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, index)

    assert result.schema_version == PRESENTATION_IR_PLANNER_SCHEMA_VERSION
    assert result.status == "ready"
    assert result.presentation_ir is not None
    payload = require_presentation_ir_payload(result.presentation_ir)
    assert payload["schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert payload["deck"]["planner_schema_version"] == PRESENTATION_IR_PLANNER_SCHEMA_VERSION
    assert payload["deck"]["slide_count"] == 5
    assert payload["slides"]
    assert all(slide["role"] for slide in payload["slides"])
    assert all("takeaway" in slide for slide in payload["slides"])
    assert all(isinstance(slide["blocks"], list) for slide in payload["slides"])
    assert all(isinstance(slide["visual_plan"], dict) for slide in payload["slides"])
    assert result.evidence_bindings
    evidence_ids = {binding.evidence_id for binding in result.evidence_bindings}
    slide_evidence_ids = {
        item["evidence_id"]
        for slide in payload["slides"]
        for item in slide.get("evidence", [])
    }
    assert slide_evidence_ids <= evidence_ids


def test_kr7f1_planner_blocks_when_source_evidence_required_but_missing() -> None:
    empty_index = OfflineEvidenceIndexBuilder().build_index([])
    request = PresentationIRPlannerRequest(
        presentation_id="pres_blocked",
        title="Unsupported market claim",
        objective="Do not invent evidence",
        require_evidence=True,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, empty_index)

    assert result.status == "blocked"
    assert result.presentation_ir is None
    assert "evidence_required_but_index_empty" in result.warnings
    assert result.errors


def test_kr7f1_prompt_only_planner_output_is_degraded_and_explicit() -> None:
    empty_index = OfflineEvidenceIndexBuilder().build_index([])
    request = PresentationIRPlannerRequest(
        presentation_id="pres_degraded",
        title="Draft without sources",
        objective="Create a draft but mark missing evidence",
        require_evidence=False,
        slide_count=3,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, empty_index)

    assert result.status == "degraded"
    assert result.presentation_ir is not None
    payload = require_presentation_ir_payload(result.presentation_ir)
    assert payload["quality_contract"]["fallback_is_degraded_and_explicit"] is True
    assert payload["quality_contract"]["requires_source_evidence"] is False
    assert all(slide["takeaway"].startswith("Evidence is not attached") or slide["role"] == "cover" for slide in payload["slides"])


def test_kr7f1_planner_does_not_require_images_or_fake_charts() -> None:
    index = _evidence_index()
    request = PresentationIRPlannerRequest(
        presentation_id="pres_safe_visuals",
        title="Automation evidence",
        objective="Summarize local evidence without fake visuals",
        slide_count=4,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, index)

    assert result.presentation_ir is not None
    payload = result.presentation_ir
    assert payload["quality_contract"]["no_fake_charts"] is True
    assert payload["quality_contract"]["no_generated_images"] is True
    assert all(slide["visual_plan"]["requires_image"] is False for slide in payload["slides"])
    assert all(slide["visual_plan"]["requires_chart"] is False for slide in payload["slides"])

def test_kr7f2_planner_emits_evidence_aware_slide_outlines() -> None:
    index = _evidence_index()
    request = PresentationIRPlannerRequest(
        presentation_id="pres_outline",
        title="Support automation results",
        objective="Support automation retention risk",
        slide_count=4,
        required_sections=("retention", "risk"),
        require_evidence=True,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, index)

    assert result.status == "ready"
    assert result.slide_outlines
    assert result.coverage_summary["schema_version"] == PRESENTATION_IR_OUTLINE_SCHEMA_VERSION
    assert result.coverage_summary["outline_coverage_ratio"] >= result.coverage_summary["required_outline_coverage_ratio"]
    assert all(outline.schema_version == PRESENTATION_IR_OUTLINE_SCHEMA_VERSION for outline in result.slide_outlines)
    assert all(outline.intent_query for outline in result.slide_outlines)
    assert all(outline.support_status == "supported" for outline in result.slide_outlines)
    assert {outline.role for outline in result.slide_outlines} >= {"cover", "retention", "risk", "closing"}
    assert result.presentation_ir is not None
    slides = result.presentation_ir["slides"]
    assert all(slide["outline"]["schema_version"] == PRESENTATION_IR_OUTLINE_SCHEMA_VERSION for slide in slides)
    assert all(slide["outline"]["support_status"] == "supported" for slide in slides)


def test_kr7f2_planner_degrades_when_outline_coverage_is_below_threshold() -> None:
    index = _evidence_index()
    request = PresentationIRPlannerRequest(
        presentation_id="pres_degraded_outline",
        title="European market growth",
        objective="European market growth margin forecast",
        slide_count=5,
        require_evidence=True,
        min_outline_coverage_ratio=1.0,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, index)

    assert result.status == "degraded"
    assert "outline_coverage_below_required_threshold" in result.warnings
    assert result.coverage_summary["outline_coverage_ratio"] < 1.0
    assert any(outline.missing_terms for outline in result.slide_outlines)
    assert result.presentation_ir is not None
    assert result.presentation_ir["quality_contract"]["evidence_aware_outline_planning"] is True
    assert result.presentation_ir["quality_contract"]["fallback_is_degraded_and_explicit"] is True


def test_kr7f2_prompt_only_outline_marks_every_slide_unsupported() -> None:
    empty_index = OfflineEvidenceIndexBuilder().build_index([])
    request = PresentationIRPlannerRequest(
        presentation_id="pres_prompt_only_outline",
        title="Draft without sources",
        objective="Create outline but mark missing evidence",
        require_evidence=False,
        slide_count=3,
    )

    result = PresentationIRPlannerFoundation().plan_from_evidence(request, empty_index)

    assert result.status == "degraded"
    assert result.coverage_summary["supported_slide_count"] == 0
    assert result.coverage_summary["unsupported_slide_count"] == 3
    assert all(outline.support_status == "unsupported" for outline in result.slide_outlines)
    assert all("slide_outline_without_evidence" in outline.warnings for outline in result.slide_outlines)
