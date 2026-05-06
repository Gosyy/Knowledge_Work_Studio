from __future__ import annotations

import json
import math
import zipfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
from typing import Literal
from xml.etree import ElementTree as ET

from backend.app.services.k_phase.renderer_quality import assess_overflow_risk
from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
from backend.app.services.slides_service.layouts import get_template_registry
from backend.app.services.slides_service.outline import PresentationPlan

K4_CHECKPOINT = "K4"
K4_SCHEMA_VERSION = "k4.visual_qa_runtime.v1"
K_PHASE_BRANCH = "8_K_Phase"
K4_BASE_AFTER_K3 = "2c57ff1bb3d8c8d911fea11555bce76d55ec800e"
RCH3_CHECKPOINT = "RCH3"
RCH3_SCHEMA_VERSION = "rch3.visual_qa_heuristic_calibration.v1"
RCH3_BASE_AFTER_RCH2 = "08430e16f347938c61acf714180f5c37896ba5d7"
P9_4_CHECKPOINT = "P9-4"
P9_4_SCHEMA_VERSION = "p9.4.visual_qa_semantic_guard.v1"
P9_4_BASE_AFTER_P9_3 = "1f546bb46de3f11f1a0a12f185bdcb1800632b18"
PPTX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
_ALLOWED_RENDER_MODES = {"adaptive", "template"}
_NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}

Severity = Literal["info", "warning", "blocker"]
VisualQAStatus = Literal["passed", "needs_operator_review", "blocked"]
ReviewDecision = Literal["approve", "request_rework", "reject"]


@dataclass(frozen=True)
class VisualQAPolicy:
    min_score_to_pass: int = 85
    min_contrast_ratio: float = 3.0
    max_warning_count_to_pass: int = 2
    max_info_count_to_pass: int = 8
    max_estimated_text_fill_ratio: float = 1.05
    blocker_text_fill_ratio: float = 1.35
    minor_overlap_ratio: float = 0.08
    major_overlap_ratio: float = 0.20
    enforce_reading_order: bool = True

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class VisualQAIssue:
    check_id: str
    severity: Severity
    slide_id: str | None
    message: str
    operator_hint: str

    def as_safe_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class VisualQAShapePreview:
    shape_id: str
    shape_name: str
    shape_kind: str
    x: int
    y: int
    cx: int
    cy: int
    text_char_count: int
    text_digest: str | None
    estimated_text_fill_ratio: float

    def as_safe_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["estimated_text_fill_ratio"] = round(self.estimated_text_fill_ratio, 3)
        return payload


@dataclass(frozen=True)
class VisualQASlidePreview:
    slide_id: str
    slide_index: int
    slide_part: str
    shape_count: int
    text_shape_count: int
    picture_shape_count: int
    bounds_ok: bool
    major_overlap_count: int
    reading_order_ok: bool
    overflow_risk_level: str
    max_estimated_text_fill_ratio: float
    reading_order_shape_ids: tuple[str, ...]

    def as_safe_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["max_estimated_text_fill_ratio"] = round(self.max_estimated_text_fill_ratio, 3)
        return payload


@dataclass(frozen=True)
class VisualQAOperatorReview:
    review_status: str
    decision: ReviewDecision | None
    operator_user_id: str
    accepted_issue_count: int
    rejected_issue_count: int
    safe_event_types: tuple[str, ...]

    def as_safe_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class VisualQARuntimeRequest:
    plan: PresentationPlan
    artifact_content: bytes
    plan_snapshot_id: str
    render_mode: str = "adaptive"
    template_id: str = "business_clean"
    artifact_filename: str = "visual-qa-deck.pptx"
    content_type: str = PPTX_CONTENT_TYPE
    policy: VisualQAPolicy = VisualQAPolicy()
    operator_user_id: str = "user_local_default"


@dataclass(frozen=True)
class VisualQAReviewRequest:
    visual_qa_result: "VisualQARuntimeResult"
    decision: ReviewDecision
    operator_user_id: str = "user_local_default"
    accepted_issue_ids: tuple[str, ...] = ()
    rejection_reason: str | None = None


@dataclass(frozen=True)
class VisualQARuntimeResult:
    status: VisualQAStatus
    score: int
    artifact_checksum_sha256: str
    slide_count: int
    policy: VisualQAPolicy
    slide_previews: tuple[VisualQASlidePreview, ...]
    issues: tuple[VisualQAIssue, ...]
    operator_review: VisualQAOperatorReview
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "score": self.score,
            "artifact_checksum_sha256": self.artifact_checksum_sha256,
            "slide_count": self.slide_count,
            "policy": self.policy.as_dict(),
            "slide_previews": [item.as_safe_dict() for item in self.slide_previews],
            "issues": [item.as_safe_dict() for item in self.issues],
            "operator_review": self.operator_review.as_safe_dict(),
            "safe_metadata": dict(self.safe_metadata),
        }


def run_visual_qa_runtime(request: VisualQARuntimeRequest) -> VisualQARuntimeResult:
    """Run local deterministic visual QA over rendered PPTX bytes.

    K4 intentionally inspects the locally generated PPTX package. It does not
    call external renderers, cloud vision models, public APIs, databases, or the
    frontend. The output is a safe preview/issue model for operator review.
    """

    _validate_request(request)
    slide_size, shape_lists = _extract_pptx_shape_previews(request.artifact_content)
    issues: list[VisualQAIssue] = []
    slide_previews: list[VisualQASlidePreview] = []

    if len(shape_lists) != len(request.plan.slides):
        issues.append(
            VisualQAIssue(
                check_id="k4.slide_count_match",
                severity="blocker",
                slide_id=None,
                message="Rendered PPTX slide count does not match approved plan slide count.",
                operator_hint="Re-render the approved plan before operator approval.",
            )
        )

    contrast_issues = _check_template_contrast(template_id=request.template_id, policy=request.policy)
    issues.extend(contrast_issues)
    semantic_issues = _check_p9_4_semantic_review_guard(request.plan)
    issues.extend(semantic_issues)

    for index, slide in enumerate(request.plan.slides, start=1):
        shapes = shape_lists[index - 1] if index - 1 < len(shape_lists) else ()
        slide_id = slide.slide_id
        bounds_issues = _check_bounds(slide_id=slide_id, shapes=shapes, slide_cx=slide_size[0], slide_cy=slide_size[1])
        overlap_issues = _check_major_overlaps(slide_id=slide_id, shapes=shapes, policy=request.policy)
        reading_order_ok, reading_order_issue = _check_reading_order(slide_id=slide_id, shapes=shapes, policy=request.policy)
        overflow_issues = _check_text_overflow(slide_id=slide_id, shapes=shapes, policy=request.policy)
        if reading_order_issue is not None:
            issues.append(reading_order_issue)
        issues.extend(bounds_issues)
        issues.extend(overlap_issues)
        issues.extend(overflow_issues)

        plan_overflow = assess_overflow_risk(slide)
        text_shapes = tuple(shape for shape in shapes if shape.shape_kind == "text")
        picture_shapes = tuple(shape for shape in shapes if shape.shape_kind == "picture")
        reading_order = tuple(shape.shape_id for shape in _reading_order_shapes(shapes))
        slide_previews.append(
            VisualQASlidePreview(
                slide_id=slide_id,
                slide_index=index,
                slide_part=f"ppt/slides/slide{index}.xml",
                shape_count=len(shapes),
                text_shape_count=len(text_shapes),
                picture_shape_count=len(picture_shapes),
                bounds_ok=not bounds_issues,
                major_overlap_count=len(overlap_issues),
                reading_order_ok=reading_order_ok,
                overflow_risk_level=plan_overflow.risk_level,
                max_estimated_text_fill_ratio=max((shape.estimated_text_fill_ratio for shape in text_shapes), default=0.0),
                reading_order_shape_ids=reading_order,
            )
        )

    score = _score_issues(issues)
    status = _status_for(score=score, issues=tuple(issues), policy=request.policy)
    operator_review = VisualQAOperatorReview(
        review_status="not_required" if status == "passed" else "required",
        decision=None,
        operator_user_id=_safe_short_text(request.operator_user_id, 80),
        accepted_issue_count=0,
        rejected_issue_count=0,
        safe_event_types=(
            "k4.visual_qa.started",
            "k4.visual_qa.preview.extracted",
            "k4.visual_qa.checks.completed",
            "k4.visual_qa.operator_review.pending" if status != "passed" else "k4.visual_qa.operator_review.not_required",
        ),
    )
    metadata = _safe_metadata(
        request=request,
        status=status,
        score=score,
        checksum=sha256(request.artifact_content).hexdigest(),
        slide_previews=tuple(slide_previews),
        issues=tuple(issues),
        operator_review=operator_review,
    )
    return VisualQARuntimeResult(
        status=status,
        score=score,
        artifact_checksum_sha256=metadata["artifact_checksum_sha256"],
        slide_count=len(slide_previews),
        policy=request.policy,
        slide_previews=tuple(slide_previews),
        issues=tuple(issues),
        operator_review=operator_review,
        safe_metadata=metadata,
    )


def build_visual_qa_operator_review(request: VisualQAReviewRequest) -> VisualQAOperatorReview:
    if request.decision not in {"approve", "request_rework", "reject"}:
        raise ValueError(f"Unsupported K4 visual QA review decision: {request.decision!r}")
    if request.decision == "approve" and any(issue.severity == "blocker" for issue in request.visual_qa_result.issues):
        raise ValueError("K4 visual QA cannot approve a result with blocker issues.")
    if request.decision in {"request_rework", "reject"} and not (request.rejection_reason or "").strip():
        raise ValueError("K4 visual QA rework/reject decisions require a safe rejection reason.")
    safe_event = {
        "approve": "k4.visual_qa.operator_review.approved",
        "request_rework": "k4.visual_qa.operator_review.rework_requested",
        "reject": "k4.visual_qa.operator_review.rejected",
    }[request.decision]
    return VisualQAOperatorReview(
        review_status="completed",
        decision=request.decision,
        operator_user_id=_safe_short_text(request.operator_user_id, 80),
        accepted_issue_count=len(request.accepted_issue_ids),
        rejected_issue_count=0 if request.decision == "approve" else len(request.visual_qa_result.issues),
        safe_event_types=("k4.visual_qa.operator_review.opened", safe_event),
    )


def build_k4_capabilities_report() -> dict[str, object]:
    return {
        "mode": "k4-visual-qa-runtime",
        "checkpoint": K4_CHECKPOINT,
        "schema_version": K4_SCHEMA_VERSION,
        "k4_base_after_k3": K4_BASE_AFTER_K3,
        "visual_qa_runtime_supported": True,
        "pptx_preview_runtime_supported": True,
        "pdf_preview_runtime_added_by_k4": False,
        "layout_bounds_check_supported": True,
        "major_overlap_check_supported": True,
        "overflow_check_supported": True,
        "contrast_check_supported": True,
        "reading_order_check_supported": True,
        "operator_review_workflow_supported": True,
        "safe_visual_qa_metadata_supported": True,
        "network_required": False,
        "cloud_vision_added_by_k4": False,
        "cloud_llm_added_by_k4": False,
        "api_endpoint_added_by_k4": False,
        "db_schema_migration_added_by_k4": False,
        "frontend_runtime_changed_by_k4": False,
        "dependency_versions_changed_by_k4": False,
        "dockerfiles_changed_by_k4": False,
        "source_to_slide_provenance_added_by_k4": False,
        "kimi_level_claimed_by_k4": False,
        "whole_project_kimi_level_supported": False,
    }


def build_rch3_capabilities_report() -> dict[str, object]:
    return {
        "rch3_checkpoint": RCH3_CHECKPOINT,
        "rch3_schema_version": RCH3_SCHEMA_VERSION,
        "rch3_base_after_rch2": RCH3_BASE_AFTER_RCH2,
        "rch3_visual_qa_heuristic_calibration_supported": True,
        "visual_qa_issue_severity_calibration_supported": True,
        "visual_qa_false_positive_reduction_supported": True,
        "visual_qa_false_negative_guard_supported": True,
        "visual_qa_info_warning_blocker_split_supported": True,
        "visual_qa_text_overflow_blocker_guard_supported": True,
        "visual_qa_minor_overlap_info_supported": True,
        "network_required_by_rch3": False,
        "api_endpoint_added_by_rch3": False,
        "db_schema_migration_added_by_rch3": False,
        "frontend_runtime_changed_by_rch3": False,
        "dependency_versions_changed_by_rch3": False,
        "dockerfiles_changed_by_rch3": False,
        "cloud_llm_added_by_rch3": False,
        "cloud_vision_added_by_rch3": False,
        "kimi_level_claimed_by_rch3": False,
        "whole_project_kimi_level_supported_by_rch3": False,
    }


def build_p9_4_capabilities_report() -> dict[str, object]:
    return {
        "p9_4_checkpoint": P9_4_CHECKPOINT,
        "p9_4_schema_version": P9_4_SCHEMA_VERSION,
        "p9_4_base_after_p9_3": P9_4_BASE_AFTER_P9_3,
        "p9_4_visual_qa_semantic_guard_supported": True,
        "visual_qa_product_quality_guard_supported": True,
        "visual_qa_semantic_issue_detection_supported": True,
        "visual_qa_generic_fallback_label_guard_supported": True,
        "visual_qa_raw_csv_rendering_guard_supported": True,
        "visual_qa_generic_table_placeholder_guard_supported": True,
        "visual_qa_arbitrary_current_target_guard_supported": True,
        "visual_qa_human_review_alignment_supported": True,
        "visual_qa_can_request_operator_review_for_semantic_issues": True,
        "network_required_by_p9_4": False,
        "api_endpoint_added_by_p9_4": False,
        "db_schema_migration_added_by_p9_4": False,
        "frontend_runtime_changed_by_p9_4": False,
        "dependency_versions_changed_by_p9_4": False,
        "dockerfiles_changed_by_p9_4": False,
        "cloud_llm_added_by_p9_4": False,
        "cloud_vision_added_by_p9_4": False,
        "kimi_level_claimed_by_p9_4": False,
        "whole_project_kimi_level_supported_by_p9_4": False,
    }


def _check_p9_4_semantic_review_guard(plan: PresentationPlan) -> tuple[VisualQAIssue, ...]:
    issues: list[VisualQAIssue] = []
    seen: set[tuple[str, str | None]] = set()
    for slide in plan.slides:
        text = _semantic_slide_text(slide)
        lowered = text.lower()
        if _has_generic_fallback_label(lowered):
            _append_semantic_issue(
                issues,
                seen,
                check_id="p9_4.generic_fallback_label",
                severity="blocker",
                slide_id=slide.slide_id,
                message="Slide uses a generic fallback/planning label that human review marked as product-quality rework.",
                operator_hint="Replace the title/body with an audience-specific, source-derived slide message before approval.",
            )
        if _has_raw_csv_rendering_signature(lowered):
            _append_semantic_issue(
                issues,
                seen,
                check_id="p9_4.raw_csv_rendering",
                severity="blocker",
                slide_id=slide.slide_id,
                message="Slide appears to render comparison-table CSV/header text instead of a decision-matrix view.",
                operator_hint="Use a structured option matrix with option, strength, weakness, recommendation, and constraint fields.",
            )
        for block in slide.blocks:
            if isinstance(block, ComparisonBlock) and _comparison_titles_are_arbitrary_current_target(block):
                _append_semantic_issue(
                    issues,
                    seen,
                    check_id="p9_4.arbitrary_current_target_layout",
                    severity="warning",
                    slide_id=slide.slide_id,
                    message="Comparison block uses arbitrary Current/Target labels that human review flagged as weak synthesis.",
                    operator_hint="Rename comparison sides to source-specific decision criteria or runtime options.",
                )
            elif isinstance(block, TableBlock) and _table_has_generic_review_placeholders(block):
                _append_semantic_issue(
                    issues,
                    seen,
                    check_id="p9_4.generic_table_review_placeholder",
                    severity="warning",
                    slide_id=slide.slide_id,
                    message="Table block contains generic review placeholders rather than operator-use evidence columns.",
                    operator_hint="Replace placeholder review cells with decision, evidence, risk, action, or owner fields.",
                )
        if _looks_like_status_deck(plan, lowered) and _missing_late_status_terms(text):
            _append_semantic_issue(
                issues,
                seen,
                check_id="p9_4.status_deck_semantic_coverage_review",
                severity="warning",
                slide_id=slide.slide_id,
                message="Status-deck content may need operator review for late-phase coverage and next-action completeness.",
                operator_hint="Confirm K4/K5/K6, closure, risks, and next actions are represented before approval.",
            )
    return tuple(issues)


def _append_semantic_issue(
    issues: list[VisualQAIssue],
    seen: set[tuple[str, str | None]],
    *,
    check_id: str,
    severity: Severity,
    slide_id: str | None,
    message: str,
    operator_hint: str,
) -> None:
    key = (check_id, slide_id)
    if key in seen:
        return
    seen.add(key)
    issues.append(
        VisualQAIssue(
            check_id=check_id,
            severity=severity,
            slide_id=slide_id,
            message=message,
            operator_hint=operator_hint,
        )
    )


def _semantic_slide_text(slide: object) -> str:
    title = getattr(slide, "title", "")
    bullets = getattr(slide, "bullets", ())
    parts = [str(title), *(str(item) for item in bullets)]
    for block in getattr(slide, "blocks", ()):  # safe structural preview only; not persisted in metadata
        if isinstance(block, ComparisonBlock):
            parts.extend((block.left_title, block.right_title, *block.left_items, *block.right_items))
        elif isinstance(block, TableBlock):
            parts.extend(block.columns)
            parts.extend(str(cell) for row in block.rows for cell in row)
            if block.caption:
                parts.append(block.caption)
    return " ".join(parts)


def _has_generic_fallback_label(lowered: str) -> bool:
    markers = (
        "k1 plan",
        "key point",
        "additional source-grounded planning point",
        "additional insight",
        "no secondary comparison point",
        "no supporting detail provided",
    )
    return any(marker in lowered for marker in markers)


def _has_raw_csv_rendering_signature(lowered: str) -> bool:
    compact = lowered.replace(" ", "")
    csv_headers = (
        "option,strength,weakness,recommendation",
        "option,strength,weakness,constraint",
        "вариант,сильнаясторона,слабаясторона,рекомендация",
    )
    if any(header in compact for header in csv_headers):
        return True
    return lowered.count(",") >= 3 and all(marker in lowered for marker in ("option", "strength", "weakness"))


def _comparison_titles_are_arbitrary_current_target(block: ComparisonBlock) -> bool:
    left = block.left_title.lower().strip()
    right = block.right_title.lower().strip()
    arbitrary_left = {"current", "current / option a", "option a", "source", "before"}
    arbitrary_right = {"target", "target / option b", "option b", "recommended next step", "after"}
    return left in arbitrary_left and right in arbitrary_right


def _table_has_generic_review_placeholders(block: TableBlock) -> bool:
    lowered_columns = tuple(column.lower().strip() for column in block.columns)
    if "review" not in lowered_columns:
        return False
    review_index = lowered_columns.index("review")
    generic_rows = 0
    for row in block.rows:
        if review_index < len(row) and str(row[review_index]).lower().strip() in {"review", "placeholder", "tbd"}:
            generic_rows += 1
    return generic_rows > 0


def _looks_like_status_deck(plan: PresentationPlan, lowered_slide_text: str) -> bool:
    plan_text = " ".join((plan.deck_title, plan.deck_goal, plan.audience)).lower()
    combined = f"{plan_text} {lowered_slide_text}"
    return any(marker in combined for marker in ("status", "project log", "milestone", "readiness", "closure"))


def _missing_late_status_terms(text: str) -> bool:
    lowered = text.lower()
    required_groups = (
        ("k4", "visual qa"),
        ("k5", "provenance"),
        ("k6", "end-to-end", "workflow"),
        ("risk", "risks", "риск"),
        ("next action", "next step", "следующ"),
    )
    matched = sum(1 for group in required_groups if any(marker in lowered for marker in group))
    return matched <= 1


def _validate_request(request: VisualQARuntimeRequest) -> None:
    if request.content_type != PPTX_CONTENT_TYPE:
        raise ValueError("K4 visual QA runtime currently accepts PPTX artifacts only.")
    if not request.artifact_content:
        raise ValueError("K4 visual QA runtime requires non-empty artifact bytes.")
    if not request.artifact_filename.endswith(".pptx"):
        raise ValueError("K4 visual QA artifact_filename must end with .pptx.")
    if request.render_mode not in _ALLOWED_RENDER_MODES:
        raise ValueError(f"Unsupported K4 render_mode: {request.render_mode!r}")
    if not request.plan_snapshot_id.strip():
        raise ValueError("K4 visual QA runtime requires a non-empty plan_snapshot_id.")
    if not request.plan.slides:
        raise ValueError("K4 visual QA runtime requires at least one planned slide.")
    if request.template_id not in get_template_registry():
        raise ValueError(f"Unsupported K4 local template_id: {request.template_id!r}")


def _extract_pptx_shape_previews(artifact_content: bytes) -> tuple[tuple[int, int], tuple[tuple[VisualQAShapePreview, ...], ...]]:
    try:
        with zipfile.ZipFile(BytesIO(artifact_content), "r") as pptx:
            names = set(pptx.namelist())
            if "ppt/presentation.xml" not in names:
                raise ValueError("PPTX package is missing ppt/presentation.xml")
            presentation = ET.fromstring(pptx.read("ppt/presentation.xml"))
            size_node = presentation.find("p:sldSz", _NS)
            slide_cx = int(size_node.attrib.get("cx", "9144000")) if size_node is not None else 9144000
            slide_cy = int(size_node.attrib.get("cy", "6858000")) if size_node is not None else 6858000
            slide_parts = sorted(
                (name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
                key=_slide_part_sort_key,
            )
            shape_lists = tuple(_extract_slide_shapes(pptx.read(part), part=part) for part in slide_parts)
            return (slide_cx, slide_cy), shape_lists
    except zipfile.BadZipFile as exc:
        raise ValueError("K4 visual QA runtime requires a valid PPTX zip package.") from exc


def _extract_slide_shapes(slide_xml: bytes, *, part: str) -> tuple[VisualQAShapePreview, ...]:
    root = ET.fromstring(slide_xml)
    previews: list[VisualQAShapePreview] = []
    for node in root.findall(".//p:sp", _NS):
        preview = _shape_preview_from_node(node, shape_kind="text")
        if preview is not None:
            previews.append(preview)
    for node in root.findall(".//p:pic", _NS):
        preview = _shape_preview_from_node(node, shape_kind="picture")
        if preview is not None:
            previews.append(preview)
    return tuple(previews)


def _shape_preview_from_node(node: ET.Element, *, shape_kind: str) -> VisualQAShapePreview | None:
    cnv = node.find(".//p:cNvPr", _NS)
    xfrm = node.find(".//a:xfrm", _NS)
    if cnv is None or xfrm is None:
        return None
    off = xfrm.find("a:off", _NS)
    ext = xfrm.find("a:ext", _NS)
    if off is None or ext is None:
        return None
    text = " ".join((item.text or "") for item in node.findall(".//a:t", _NS)).strip()
    font_sizes = [int(rpr.attrib.get("sz", "1600")) for rpr in node.findall(".//a:rPr", _NS) if rpr.attrib.get("sz")]
    font_size = max(font_sizes) if font_sizes else 1600
    cx = int(ext.attrib.get("cx", "0"))
    cy = int(ext.attrib.get("cy", "0"))
    text_char_count = len(text)
    fill_ratio = _estimate_text_fill_ratio(text_char_count=text_char_count, cx=cx, cy=cy, font_size=font_size)
    shape_id = str(cnv.attrib.get("id", "0"))
    shape_name = _safe_short_text(str(cnv.attrib.get("name", f"shape-{shape_id}")), 120)
    return VisualQAShapePreview(
        shape_id=shape_id,
        shape_name=shape_name,
        shape_kind=shape_kind if shape_kind == "picture" else ("text" if text_char_count else "shape"),
        x=int(off.attrib.get("x", "0")),
        y=int(off.attrib.get("y", "0")),
        cx=cx,
        cy=cy,
        text_char_count=text_char_count,
        text_digest=("sha256:" + sha256(text.encode("utf-8")).hexdigest()) if text else None,
        estimated_text_fill_ratio=fill_ratio,
    )


def _check_bounds(*, slide_id: str, shapes: tuple[VisualQAShapePreview, ...], slide_cx: int, slide_cy: int) -> list[VisualQAIssue]:
    issues: list[VisualQAIssue] = []
    for shape in shapes:
        if shape.x < 0 or shape.y < 0 or shape.cx <= 0 or shape.cy <= 0 or shape.x + shape.cx > slide_cx or shape.y + shape.cy > slide_cy:
            issues.append(
                VisualQAIssue(
                    check_id="k4.layout_bounds",
                    severity="blocker",
                    slide_id=slide_id,
                    message=f"Shape {shape.shape_id} is outside the slide bounds.",
                    operator_hint="Re-run renderer quality or select a safer local layout before approval.",
                )
            )
    return issues


def _check_major_overlaps(*, slide_id: str, shapes: tuple[VisualQAShapePreview, ...], policy: VisualQAPolicy) -> list[VisualQAIssue]:
    issues: list[VisualQAIssue] = []
    relevant = tuple(shape for shape in shapes if shape.shape_kind in {"text", "picture"})
    for left_index, left in enumerate(relevant):
        for right in relevant[left_index + 1 :]:
            if _allowed_overlap(left, right):
                continue
            ratio = _overlap_ratio(left, right)
            if ratio > policy.major_overlap_ratio:
                issues.append(
                    VisualQAIssue(
                        check_id="k4.major_overlap",
                        severity="warning",
                        slide_id=slide_id,
                        message=f"Shapes {left.shape_id} and {right.shape_id} overlap above calibrated warning threshold.",
                        operator_hint="Inspect the slide preview and choose a less dense layout if needed.",
                    )
                )
            elif ratio > policy.minor_overlap_ratio:
                issues.append(
                    VisualQAIssue(
                        check_id="rch3.minor_overlap_info",
                        severity="info",
                        slide_id=slide_id,
                        message=f"Shapes {left.shape_id} and {right.shape_id} have minor calibrated overlap.",
                        operator_hint="No automatic rework is required unless the operator sees a visual problem.",
                    )
                )
    return issues

def _check_text_overflow(*, slide_id: str, shapes: tuple[VisualQAShapePreview, ...], policy: VisualQAPolicy) -> list[VisualQAIssue]:
    issues: list[VisualQAIssue] = []
    for shape in shapes:
        if shape.shape_kind != "text":
            continue
        if shape.estimated_text_fill_ratio > policy.blocker_text_fill_ratio:
            issues.append(
                VisualQAIssue(
                    check_id="rch3.text_overflow_blocker_guard",
                    severity="blocker",
                    slide_id=slide_id,
                    message=f"Shape {shape.shape_id} is very likely to overflow its text box.",
                    operator_hint="Shorten the slide text or re-run K3 density controls before approval.",
                )
            )
        elif shape.estimated_text_fill_ratio > policy.max_estimated_text_fill_ratio:
            issues.append(
                VisualQAIssue(
                    check_id="k4.estimated_text_overflow",
                    severity="warning",
                    slide_id=slide_id,
                    message=f"Shape {shape.shape_id} may overflow its text box.",
                    operator_hint="Shorten the slide text or re-run K3 density controls before approval.",
                )
            )
    return issues

def _check_reading_order(*, slide_id: str, shapes: tuple[VisualQAShapePreview, ...], policy: VisualQAPolicy) -> tuple[bool, VisualQAIssue | None]:
    if not policy.enforce_reading_order:
        return True, None
    text_shapes = tuple(shape for shape in shapes if shape.shape_kind == "text" and shape.text_char_count > 0)
    if len(text_shapes) <= 1:
        return True, None
    first = text_shapes[0]
    topmost = min(text_shapes, key=lambda shape: (shape.y, shape.x, int(shape.shape_id) if shape.shape_id.isdigit() else 0))
    if first.shape_id != topmost.shape_id and "title" not in first.shape_name.lower():
        return False, VisualQAIssue(
            check_id="k4.reading_order",
            severity="warning",
            slide_id=slide_id,
            message="The first text shape is not the title/topmost readable shape.",
            operator_hint="Review the slide reading order before export or handoff.",
        )
    return True, None


def _check_template_contrast(*, template_id: str, policy: VisualQAPolicy) -> tuple[VisualQAIssue, ...]:
    template = get_template_registry()[template_id]
    checks = (
        ("title", template.title_color, template.background_color),
        ("body", template.body_color, template.background_color),
        ("accent", template.accent_color, template.background_color),
    )
    issues: list[VisualQAIssue] = []
    for label, foreground, background in checks:
        ratio = _contrast_ratio(foreground, background)
        if ratio < policy.min_contrast_ratio:
            issues.append(
                VisualQAIssue(
                    check_id="k4.contrast",
                    severity="blocker",
                    slide_id=None,
                    message=f"Template {template_id} {label} contrast is below policy.",
                    operator_hint="Use a bundled local theme with stronger contrast before approval.",
                )
            )
    return tuple(issues)


def _score_issues(issues: tuple[VisualQAIssue, ...] | list[VisualQAIssue]) -> int:
    score = 100
    for issue in issues:
        score -= 35 if issue.severity == "blocker" else 8 if issue.severity == "warning" else 1
    return max(0, min(100, score))


def _status_for(*, score: int, issues: tuple[VisualQAIssue, ...], policy: VisualQAPolicy) -> VisualQAStatus:
    counts = _issue_counts_by_severity(issues)
    if counts["blocker"] > 0:
        return "blocked"
    if score < policy.min_score_to_pass or counts["warning"] > policy.max_warning_count_to_pass:
        return "needs_operator_review"
    if counts["info"] > policy.max_info_count_to_pass and score < 95:
        return "needs_operator_review"
    return "passed"


def _issue_counts_by_severity(issues: tuple[VisualQAIssue, ...] | list[VisualQAIssue]) -> dict[str, int]:
    counts = {"info": 0, "warning": 0, "blocker": 0}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return counts


def _safe_metadata(
    *,
    request: VisualQARuntimeRequest,
    status: VisualQAStatus,
    score: int,
    checksum: str,
    slide_previews: tuple[VisualQASlidePreview, ...],
    issues: tuple[VisualQAIssue, ...],
    operator_review: VisualQAOperatorReview,
) -> dict[str, object]:
    metadata = {
        **build_k4_capabilities_report(),
        "plan_snapshot_id": _safe_short_text(request.plan_snapshot_id, 120),
        "artifact_filename": _safe_filename(request.artifact_filename),
        "artifact_checksum_sha256": checksum,
        "artifact_size_bytes": len(request.artifact_content),
        "render_mode": request.render_mode,
        "template_id": request.template_id,
        "slide_count": len(slide_previews),
        "score": score,
        "status": status,
        "issue_count": len(issues),
        "blocker_count": sum(1 for issue in issues if issue.severity == "blocker"),
        "warning_count": sum(1 for issue in issues if issue.severity == "warning"),
        "info_count": sum(1 for issue in issues if issue.severity == "info"),
        "calibrated_issue_counts": _issue_counts_by_severity(issues),
        "operator_review_required": operator_review.review_status == "required",
        "slide_preview_count": len(slide_previews),
        "max_estimated_text_fill_ratio": round(max((item.max_estimated_text_fill_ratio for item in slide_previews), default=0.0), 3),
        "reading_order_ok": all(item.reading_order_ok for item in slide_previews),
        "bounds_ok": all(item.bounds_ok for item in slide_previews),
        "semantic_review_guard_issue_count": sum(1 for issue in issues if issue.check_id.startswith("p9_4.")),
        "semantic_review_guard_warning_count": sum(1 for issue in issues if issue.check_id.startswith("p9_4.") and issue.severity == "warning"),
        "semantic_review_guard_blocker_count": sum(1 for issue in issues if issue.check_id.startswith("p9_4.") and issue.severity == "blocker"),
        **build_p9_4_capabilities_report(),
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "raw_slide_text_stored": False,
        "raw_sensitive_values_stored": False,
        **build_rch3_capabilities_report(),
    }
    json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    return metadata


def _estimate_text_fill_ratio(*, text_char_count: int, cx: int, cy: int, font_size: int) -> float:
    if text_char_count <= 0 or cx <= 0 or cy <= 0 or font_size <= 0:
        return 0.0
    avg_char_width_emu = max(1.0, font_size * 54.0)
    line_height_emu = max(1.0, font_size * 150.0)
    chars_per_line = max(1.0, cx / avg_char_width_emu)
    line_count = max(1.0, cy / line_height_emu)
    capacity = chars_per_line * line_count
    return round(text_char_count / capacity, 4)


def _reading_order_shapes(shapes: tuple[VisualQAShapePreview, ...]) -> tuple[VisualQAShapePreview, ...]:
    return tuple(shape for shape in shapes if shape.shape_kind == "text" and shape.text_char_count > 0)


def _overlap_ratio(left: VisualQAShapePreview, right: VisualQAShapePreview) -> float:
    x_overlap = max(0, min(left.x + left.cx, right.x + right.cx) - max(left.x, right.x))
    y_overlap = max(0, min(left.y + left.cy, right.y + right.cy) - max(left.y, right.y))
    overlap = x_overlap * y_overlap
    if overlap <= 0:
        return 0.0
    left_area = max(1, left.cx * left.cy)
    right_area = max(1, right.cx * right.cy)
    return overlap / min(left_area, right_area)


def _allowed_overlap(left: VisualQAShapePreview, right: VisualQAShapePreview) -> bool:
    names = f"{left.shape_name} {right.shape_name}".lower()
    return "caption" in names or "table_block" in names or "chart_block" in names


def _contrast_ratio(foreground: str, background: str) -> float:
    fg = _relative_luminance(foreground)
    bg = _relative_luminance(background)
    lighter = max(fg, bg)
    darker = min(fg, bg)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def _relative_luminance(hex_color: str) -> float:
    values = _hex_to_rgb(hex_color)

    def channel(value: int) -> float:
        normalized = value / 255.0
        if normalized <= 0.03928:
            return normalized / 12.92
        return math.pow((normalized + 0.055) / 1.055, 2.4)

    red, green, blue = (channel(value) for value in values)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    cleaned = hex_color.strip().lstrip("#")
    if len(cleaned) != 6:
        raise ValueError(f"Unsupported K4 hex color: {hex_color!r}")
    return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)


def _slide_part_sort_key(name: str) -> int:
    stem = name.rsplit("/", 1)[-1].removeprefix("slide").removesuffix(".xml")
    return int(stem) if stem.isdigit() else 0


def _safe_short_text(value: str, max_length: int) -> str:
    cleaned = " ".join(str(value).replace("\n", " ").split())
    return cleaned[:max_length]


def _safe_filename(value: str) -> str:
    cleaned = _safe_short_text(value, 160)
    if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
        raise ValueError("K4 visual QA artifact_filename must be a safe local filename.")
    return cleaned
