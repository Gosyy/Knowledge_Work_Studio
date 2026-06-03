from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any, Iterable, Literal

from backend.app.services.slides_service.data_backed_charts import DataBackedChartResult, sample_data_backed_chart_report
from backend.app.services.slides_service.professional_layout_engine import ProfessionalLayoutResult, sample_professional_layout_report
from backend.app.services.slides_service.source_image_selection import SourceImageSelectionResult, sample_source_image_selection_report

PROFESSIONAL_QUALITY_SCHEMA_VERSION = "presentation_professional_quality_evaluator.v1"
PROFESSIONAL_QUALITY_PHASE = "KR-7N professional quality evaluator"

ProfessionalQualityStatus = Literal["ready", "degraded", "blocked"]
QualityAxis = Literal["content", "design", "coherence", "data", "assets", "export"]

_FILLER_RE = re.compile(r"\b(?:lorem|ipsum|placeholder|todo|tbd|пример|заполнитель)\b", re.IGNORECASE | re.UNICODE)


@dataclass(frozen=True)
class ProfessionalQualityAxisScore:
    axis: QualityAxis
    score: float
    status: ProfessionalQualityStatus
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True)
class ProfessionalQualityReport:
    schema_version: str
    phase: str
    status: ProfessionalQualityStatus
    professional_quality_evaluator_implemented: bool
    quality_report_built: bool
    quality_pass: bool
    degraded_deck: bool
    overall_score: float
    pass_threshold: float
    axis_scores: tuple[ProfessionalQualityAxisScore, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    content_quality_evaluated: bool = True
    design_quality_evaluated: bool = True
    coherence_quality_evaluated: bool = True
    data_quality_evaluated: bool = True
    asset_quality_evaluated: bool = True
    export_quality_evaluated: bool = True
    score_deterministic: bool = True
    quality_report_schema_written: bool = True
    kimi_level_professional_status_requires_quality_pass: bool = True
    degraded_decks_marked_degraded: bool = True
    visual_qa_runtime_executed: bool = False
    rendered_png_qa_executed: bool = False
    renderer_runtime_changed: bool = False
    frontend_runtime_changed: bool = False
    gigachat_runtime_changed: bool = False
    docker_deploy_postgres_changed: bool = False
    production_quality_claimed: bool = False
    kimi_level_quality_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "status": self.status,
            "professional_quality_evaluator_implemented": self.professional_quality_evaluator_implemented,
            "quality_report_built": self.quality_report_built,
            "quality_pass": self.quality_pass,
            "degraded_deck": self.degraded_deck,
            "overall_score": self.overall_score,
            "pass_threshold": self.pass_threshold,
            "axis_scores": [axis.as_dict() for axis in self.axis_scores],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "content_quality_evaluated": self.content_quality_evaluated,
            "design_quality_evaluated": self.design_quality_evaluated,
            "coherence_quality_evaluated": self.coherence_quality_evaluated,
            "data_quality_evaluated": self.data_quality_evaluated,
            "asset_quality_evaluated": self.asset_quality_evaluated,
            "export_quality_evaluated": self.export_quality_evaluated,
            "score_deterministic": self.score_deterministic,
            "quality_report_schema_written": self.quality_report_schema_written,
            "kimi_level_professional_status_requires_quality_pass": self.kimi_level_professional_status_requires_quality_pass,
            "degraded_decks_marked_degraded": self.degraded_decks_marked_degraded,
            "visual_qa_runtime_executed": self.visual_qa_runtime_executed,
            "rendered_png_qa_executed": self.rendered_png_qa_executed,
            "renderer_runtime_changed": self.renderer_runtime_changed,
            "frontend_runtime_changed": self.frontend_runtime_changed,
            "gigachat_runtime_changed": self.gigachat_runtime_changed,
            "docker_deploy_postgres_changed": self.docker_deploy_postgres_changed,
            "production_quality_claimed": self.production_quality_claimed,
            "kimi_level_quality_claimed": self.kimi_level_quality_claimed,
            "non_goals": [
                "no_visual_qa_runtime_execution",
                "no_rendered_png_quality_scoring",
                "no_renderer_runtime_changes",
                "no_frontend_runtime_changes",
                "no_gigachat_runtime_changes",
                "no_docker_deploy_postgres_changes",
                "no_production_quality_claim",
                "no_kimi_level_quality_claim",
            ],
        }


def evaluate_professional_quality(
    *,
    deck_title: str,
    objective: str,
    slide_titles: Iterable[str],
    slide_roles: Iterable[str],
    evidence_refs: Iterable[str] = (),
    layout_result: ProfessionalLayoutResult | dict[str, Any] | None = None,
    data_backed_charts: DataBackedChartResult | dict[str, Any] | None = None,
    source_image_selection: SourceImageSelectionResult | dict[str, Any] | None = None,
    export_proof_bundle: dict[str, Any] | None = None,
    pass_threshold: float = 0.82,
) -> ProfessionalQualityReport:
    """Evaluate professional deck quality from source-backed contract reports.

    KR-7N creates a deterministic quality report schema. It does not execute
    rendered PNG visual QA, modify renderer/runtime code, or claim Kimi-level
    quality. Export quality is based only on an already-produced proof bundle.
    """

    titles = tuple(str(title).strip() for title in slide_titles if str(title).strip())
    roles = tuple(str(role).strip() for role in slide_roles if str(role).strip())
    refs = tuple(str(ref).strip() for ref in evidence_refs if str(ref).strip())
    layout_payload = _as_dict(layout_result)
    chart_payload = _as_dict(data_backed_charts)
    image_payload = _as_dict(source_image_selection)
    export_payload = dict(export_proof_bundle or {})

    axes = (
        _score_content(deck_title=deck_title, objective=objective, slide_titles=titles, evidence_refs=refs),
        _score_design(layout_payload),
        _score_coherence(slide_titles=titles, slide_roles=roles),
        _score_data(chart_payload),
        _score_assets(image_payload),
        _score_export(export_payload),
    )
    blockers = tuple(_unique(blocker for axis in axes for blocker in axis.blockers))
    warnings = tuple(_unique(warning for axis in axes for warning in axis.warnings))
    overall_score = round(mean(axis.score for axis in axes), 3) if axes else 0.0
    if blockers:
        status: ProfessionalQualityStatus = "blocked"
    elif overall_score < pass_threshold or warnings:
        status = "degraded"
    else:
        status = "ready"
    quality_pass = status == "ready" and overall_score >= pass_threshold and not blockers

    return ProfessionalQualityReport(
        schema_version=PROFESSIONAL_QUALITY_SCHEMA_VERSION,
        phase=PROFESSIONAL_QUALITY_PHASE,
        status=status,
        professional_quality_evaluator_implemented=True,
        quality_report_built=True,
        quality_pass=quality_pass,
        degraded_deck=status == "degraded",
        overall_score=overall_score,
        pass_threshold=pass_threshold,
        axis_scores=axes,
        blockers=blockers,
        warnings=warnings,
    )


def sample_professional_quality_report() -> dict[str, Any]:
    layout_report = sample_professional_layout_report()
    chart_report = sample_data_backed_chart_report()
    image_report = sample_source_image_selection_report()
    selected_bindings = [binding for binding in image_report.get("slide_bindings", []) if binding.get("status") == "selected"]
    image_report = dict(image_report)
    image_report["slide_bindings"] = selected_bindings
    image_report["selected_image_count"] = len(selected_bindings)
    image_report["status"] = "ready"
    proof_bundle = sample_export_proof_bundle_report()
    report = evaluate_professional_quality(
        deck_title="Market evidence dashboard",
        objective="Explain source-backed revenue, retention and risk signals for leadership decision making.",
        slide_titles=("Market evidence dashboard", "Quarterly revenue and cost", "Source-backed asset relevance"),
        slide_roles=("title", "data", "insight"),
        evidence_refs=(
            "uploaded_finance_workbook#xlsx-sheet:1!A1:C5",
            "uploaded_brand_deck#slide:3#image:product_photo",
            "kr7h11-proof-bundle#pdf_png_proof",
        ),
        layout_result=layout_report,
        data_backed_charts=chart_report,
        source_image_selection=image_report,
        export_proof_bundle=proof_bundle,
    )
    return report.as_dict()


def sample_export_proof_bundle_report() -> dict[str, Any]:
    return {
        "schema_version": "presentation_renderer_worker_libreoffice_proof_bundle.v1",
        "status": "ready",
        "artifact_bundle_verified": True,
        "proof_bundle_produced": True,
        "proof_bundle_verified": True,
        "pdf_proof_exists": True,
        "pdf_proof_file_size_nonzero": True,
        "png_proof_count": 2,
        "png_proof_basenames": ["slide_01.png", "slide_02.png"],
        "fake_proof_used": False,
        "fallback_renderer_used": False,
        "python_pptx_proof_used": False,
        "visual_qa_executed": False,
    }


def _score_content(*, deck_title: str, objective: str, slide_titles: tuple[str, ...], evidence_refs: tuple[str, ...]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 1.0
    if not deck_title.strip():
        blockers.append("content_missing_deck_title")
        score -= 0.25
    if len(objective.strip()) < 24:
        blockers.append("content_missing_clear_objective")
        score -= 0.3
    if not slide_titles:
        blockers.append("content_missing_slide_titles")
        score -= 0.2
    if not evidence_refs:
        blockers.append("content_missing_evidence_refs")
        score -= 0.25
    if any(_FILLER_RE.search(title or "") for title in slide_titles):
        warnings.append("content_contains_filler_or_placeholder_text")
        score -= 0.15
    return _axis("content", score, blockers, warnings, evidence_refs)


def _score_design(layout: dict[str, Any]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    score = 1.0
    if not layout:
        blockers.append("design_missing_professional_layout_report")
        return _axis("design", 0.0, blockers, warnings, evidence)
    if layout.get("schema_version") != "presentation_professional_layout_engine.v1":
        blockers.append("design_layout_report_schema_mismatch")
        score -= 0.35
    if layout.get("status") == "blocked":
        blockers.append("design_layout_report_blocked")
        score -= 0.5
    elif layout.get("status") == "degraded":
        warnings.append("design_layout_report_degraded")
        score -= 0.15
    plans = layout.get("slide_plans") or []
    for plan in plans:
        evidence.append(f"layout:{plan.get('slide_id', 'unknown')}")
        if plan.get("overlap_count", 0) > 0:
            blockers.append(f"design_overlap_detected:{plan.get('slide_id', 'unknown')}")
            score -= 0.2
        if plan.get("title_clipped") is True:
            blockers.append(f"design_title_clipped:{plan.get('slide_id', 'unknown')}")
            score -= 0.2
        layout_score = plan.get("layout_score")
        if isinstance(layout_score, (int, float)) and layout_score < 0.7:
            warnings.append(f"design_low_layout_score:{plan.get('slide_id', 'unknown')}")
            score -= 0.05
    for field in ("visual_qa_executed", "rendered_png_qa_executed", "production_layout_claimed", "kimi_level_quality_claimed"):
        if layout.get(field) is True:
            blockers.append(f"design_forbidden_upstream_claim:{field}")
            score -= 0.2
    return _axis("design", score, blockers, warnings, evidence)


def _score_coherence(*, slide_titles: tuple[str, ...], slide_roles: tuple[str, ...]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 1.0
    if not slide_roles:
        blockers.append("coherence_missing_slide_roles")
        score -= 0.25
    if slide_roles and slide_roles[0] not in {"title", "cover", "executive_summary"}:
        warnings.append("coherence_first_slide_role_not_opening")
        score -= 0.1
    normalized_titles = [re.sub(r"\s+", " ", title.strip().lower()) for title in slide_titles if title.strip()]
    duplicate_titles = sorted({title for title in normalized_titles if normalized_titles.count(title) > 1})
    if duplicate_titles:
        warnings.append("coherence_repeated_slide_titles")
        score -= 0.12
    if len(slide_roles) >= 3 and len(set(slide_roles)) == 1:
        warnings.append("coherence_all_slide_roles_identical")
        score -= 0.1
    return _axis("coherence", score, blockers, warnings, ())


def _score_data(charts: dict[str, Any]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    score = 1.0
    if not charts:
        warnings.append("data_no_chart_report_provided")
        return _axis("data", 0.78, blockers, warnings, evidence)
    if charts.get("schema_version") != "presentation_data_backed_charts.v1":
        blockers.append("data_chart_report_schema_mismatch")
        score -= 0.35
    if charts.get("status") == "blocked":
        blockers.append("data_chart_binding_blocked")
        score -= 0.45
    for flag in ("fake_chart_data_allowed", "generated_chart_data_allowed", "random_chart_data_allowed", "bullet_length_charts_allowed", "chart_without_data_source_allowed"):
        if charts.get(flag) is True:
            blockers.append(f"data_forbidden_chart_source:{flag}")
            score -= 0.2
    if charts.get("source_refs_required") is not True:
        blockers.append("data_source_refs_not_required")
        score -= 0.2
    bindings = charts.get("chart_bindings") or charts.get("bindings") or []
    for binding in bindings:
        if binding.get("status") == "blocked":
            blockers.append(f"data_chart_binding_blocked:{binding.get('block_id', 'unknown')}")
        for key in ("source_id", "data_ref", "provenance_ref"):
            value = binding.get(key) or binding.get("source", {}).get(key)
            if value:
                evidence.append(str(value))
    if not evidence and charts.get("bound_chart_count", 0):
        blockers.append("data_bound_charts_missing_provenance")
        score -= 0.2
    if charts.get("native_chart_rendering_implemented") is True:
        blockers.append("data_native_chart_rendering_claimed_too_early")
        score -= 0.15
    return _axis("data", score, blockers, warnings, evidence)


def _score_assets(images: dict[str, Any]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    score = 1.0
    if not images:
        warnings.append("assets_no_source_image_selection_report_provided")
        return _axis("assets", 0.78, blockers, warnings, evidence)
    if images.get("schema_version") != "presentation_source_image_selection.v1":
        blockers.append("assets_source_image_selection_schema_mismatch")
        score -= 0.3
    if images.get("source_images_only_enforced") is not True:
        blockers.append("assets_source_images_only_not_enforced")
        score -= 0.3
    for flag in ("generated_images_allowed", "fallback_images_allowed", "fake_artifacts_allowed", "external_images_allowed", "inline_image_payloads_allowed"):
        if images.get(flag) is True:
            blockers.append(f"assets_forbidden_image_source:{flag}")
            score -= 0.2
    for binding in images.get("slide_bindings", []):
        if binding.get("status") == "selected":
            ref = binding.get("provenance_ref") or binding.get("evidence_ref") or binding.get("source_ref")
            if ref:
                evidence.append(str(ref))
            else:
                blockers.append(f"assets_selected_image_missing_provenance:{binding.get('slide_id', 'unknown')}")
        elif binding.get("status") == "typographic_fallback":
            warnings.append(f"assets_typographic_fallback:{binding.get('slide_id', 'unknown')}")
            score -= 0.05
    return _axis("assets", score, blockers, warnings, evidence)


def _score_export(proof: dict[str, Any]) -> ProfessionalQualityAxisScore:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    score = 1.0
    if not proof:
        blockers.append("export_missing_pdf_png_proof_bundle")
        return _axis("export", 0.0, blockers, warnings, evidence)
    if proof.get("schema_version") != "presentation_renderer_worker_libreoffice_proof_bundle.v1":
        blockers.append("export_proof_bundle_schema_mismatch")
        score -= 0.35
    for field in ("artifact_bundle_verified", "proof_bundle_produced", "proof_bundle_verified", "pdf_proof_exists", "pdf_proof_file_size_nonzero"):
        if proof.get(field) is not True:
            blockers.append(f"export_missing_required_proof_field:{field}")
            score -= 0.12
    if not isinstance(proof.get("png_proof_count"), int) or proof.get("png_proof_count", 0) < 1:
        blockers.append("export_missing_png_slide_proofs")
        score -= 0.2
    for field in ("fake_proof_used", "fallback_renderer_used", "python_pptx_proof_used", "visual_qa_executed"):
        if proof.get(field) is True:
            blockers.append(f"export_forbidden_proof_claim:{field}")
            score -= 0.2
    evidence.append("libreoffice_pdf_png_proof_bundle")
    return _axis("export", score, blockers, warnings, evidence)


def _axis(axis: QualityAxis, score: float, blockers: list[str] | tuple[str, ...], warnings: list[str] | tuple[str, ...], evidence_refs: Iterable[str]) -> ProfessionalQualityAxisScore:
    normalized = max(0.0, min(1.0, round(score, 3)))
    blocker_tuple = tuple(_unique(blockers))
    warning_tuple = tuple(_unique(warnings))
    if blocker_tuple:
        status: ProfessionalQualityStatus = "blocked"
    elif warning_tuple or normalized < 0.82:
        status = "degraded"
    else:
        status = "ready"
    return ProfessionalQualityAxisScore(axis=axis, score=normalized, status=status, blockers=blocker_tuple, warnings=warning_tuple, evidence_refs=tuple(_unique(evidence_refs)))


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        payload = as_dict()
        return payload if isinstance(payload, dict) else {}
    return {}


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
