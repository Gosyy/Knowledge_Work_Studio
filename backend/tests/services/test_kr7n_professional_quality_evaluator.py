from __future__ import annotations

from backend.app.services.slides_service import (
    PROFESSIONAL_QUALITY_SCHEMA_VERSION,
    evaluate_professional_quality,
    sample_professional_quality_report,
)
from backend.app.services.slides_service.professional_layout_engine import ProfessionalLayoutSlideRequest, sample_professional_layout_report, solve_professional_layout
from backend.app.services.slides_service.professional_quality_evaluator import sample_export_proof_bundle_report
from backend.app.services.slides_service.data_backed_charts import sample_data_backed_chart_report
from backend.app.services.slides_service.source_image_selection import sample_source_image_selection_report
from backend.app.services.slides_service.template_brand_profile import sample_template_brand_profile_report


def _ready_report() -> dict[str, object]:
    return sample_professional_quality_report()


def test_kr7n_sample_quality_report_is_ready_and_does_not_claim_kimi_level() -> None:
    report = _ready_report()

    assert report["schema_version"] == PROFESSIONAL_QUALITY_SCHEMA_VERSION
    assert report["status"] == "ready"
    assert report["quality_pass"] is True
    assert report["degraded_deck"] is False
    assert report["overall_score"] >= report["pass_threshold"]
    assert {axis["axis"] for axis in report["axis_scores"]} == {"content", "design", "coherence", "data", "assets", "export"}
    assert report["production_quality_claimed"] is False
    assert report["kimi_level_quality_claimed"] is False
    assert report["visual_qa_runtime_executed"] is False
    assert report["renderer_runtime_changed"] is False


def test_kr7n_blocks_missing_objective_and_evidence_refs() -> None:
    report = evaluate_professional_quality(
        deck_title="Quarterly update",
        objective="",
        slide_titles=("Quarterly update",),
        slide_roles=("title",),
        evidence_refs=(),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=sample_source_image_selection_report(),
        export_proof_bundle=sample_export_proof_bundle_report(),
    ).as_dict()

    assert report["status"] == "blocked"
    assert report["quality_pass"] is False
    assert "content_missing_clear_objective" in report["blockers"]
    assert "content_missing_evidence_refs" in report["blockers"]


def test_kr7n_blocks_design_with_clipped_title() -> None:
    impossible_title = " ".join(["ExtremelyLongUnbreakableTitleToken"] * 100)
    bad_layout = solve_professional_layout(
        [ProfessionalLayoutSlideRequest(slide_id="s_bad", role="content", title=impossible_title)],
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()

    report = evaluate_professional_quality(
        deck_title="Layout risk",
        objective="Show that impossible titles block professional quality acceptance.",
        slide_titles=(impossible_title,),
        slide_roles=("title",),
        evidence_refs=("layout:test",),
        layout_result=bad_layout,
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=sample_source_image_selection_report(),
        export_proof_bundle=sample_export_proof_bundle_report(),
    ).as_dict()

    assert report["status"] == "blocked"
    assert any(str(blocker).startswith("design_title_clipped") for blocker in report["blockers"])


def test_kr7n_blocks_fake_or_generated_chart_data_claims() -> None:
    chart_report = sample_data_backed_chart_report()
    chart_report["generated_chart_data_allowed"] = True

    report = evaluate_professional_quality(
        deck_title="Data integrity",
        objective="Ensure generated chart data cannot pass professional quality gates.",
        slide_titles=("Data integrity", "Revenue chart"),
        slide_roles=("title", "data"),
        evidence_refs=("uploaded_finance_workbook#xlsx-sheet:1!A1:C5",),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=chart_report,
        source_image_selection=sample_source_image_selection_report(),
        export_proof_bundle=sample_export_proof_bundle_report(),
    ).as_dict()

    assert report["status"] == "blocked"
    assert "data_forbidden_chart_source:generated_chart_data_allowed" in report["blockers"]


def test_kr7n_blocks_missing_export_proof_bundle() -> None:
    report = evaluate_professional_quality(
        deck_title="Export proof",
        objective="Professional quality requires verified PDF and PNG proof bundle evidence.",
        slide_titles=("Export proof",),
        slide_roles=("title",),
        evidence_refs=("evidence:export",),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=sample_source_image_selection_report(),
        export_proof_bundle=None,
    ).as_dict()

    assert report["status"] == "blocked"
    assert report["quality_pass"] is False
    assert "export_missing_pdf_png_proof_bundle" in report["blockers"]


def test_kr7n_marks_degraded_deck_without_optional_assets_not_fake_success() -> None:
    image_report = sample_source_image_selection_report()
    image_report["slide_bindings"] = [
        {
            "slide_id": "s_no_asset",
            "status": "typographic_fallback",
            "reason": "no relevant source image",
        }
    ]

    report = evaluate_professional_quality(
        deck_title="Typographic fallback",
        objective="Mark decks degraded when source assets are unavailable instead of pretending fake image success.",
        slide_titles=("Typographic fallback", "Asset gap"),
        slide_roles=("title", "insight"),
        evidence_refs=("evidence:asset-gap",),
        layout_result=sample_professional_layout_report(),
        data_backed_charts=sample_data_backed_chart_report(),
        source_image_selection=image_report,
        export_proof_bundle=sample_export_proof_bundle_report(),
    ).as_dict()

    assert report["status"] == "degraded"
    assert report["quality_pass"] is False
    assert report["degraded_deck"] is True
    assert any(str(warning).startswith("assets_typographic_fallback") for warning in report["warnings"])
