from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

from backend.app.services.slides_service.data_backed_charts import DataBackedChartResult, DataChartBinding, sample_data_backed_chart_report
from backend.app.services.slides_service.source_image_selection import SourceImageSelectionResult, SourceImageSlideBinding, sample_source_image_selection_report
from backend.app.services.slides_service.template_brand_profile import TemplateBrandProfileResult, sample_template_brand_profile_report

PROFESSIONAL_LAYOUT_SCHEMA_VERSION = "presentation_professional_layout_engine.v1"
PROFESSIONAL_LAYOUT_PHASE = "KR-7L professional layout engine"

ProfessionalLayoutStatus = Literal["ready", "degraded", "blocked"]
ProfessionalLayoutBlockType = Literal["title", "body", "image", "chart", "footer"]
ProfessionalLayoutBlockStatus = Literal["placed", "typographic_fallback", "blocked"]

EMU_PER_INCH = 914400
DEFAULT_SLIDE_WIDTH_EMU = 13_166_667
DEFAULT_SLIDE_HEIGHT_EMU = 7_500_000
_DEFAULT_MARGIN_EMU = 457_200
_DEFAULT_GUTTER_EMU = 228_600
_GRID_COLUMNS = 12
_GRID_ROWS = 8
_MIN_TITLE_FONT_PT = 24.0
_MIN_BODY_FONT_PT = 14.0
_MAX_DENSITY = 0.82
_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]+", flags=re.UNICODE)


@dataclass(frozen=True)
class ProfessionalLayoutBox:
    x: int
    y: int
    cx: int
    cy: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)

    @property
    def right(self) -> int:
        return self.x + self.cx

    @property
    def bottom(self) -> int:
        return self.y + self.cy

    @property
    def area(self) -> int:
        return max(0, self.cx) * max(0, self.cy)


@dataclass(frozen=True)
class ProfessionalLayoutBlock:
    block_id: str
    block_type: ProfessionalLayoutBlockType
    role: str
    status: ProfessionalLayoutBlockStatus
    box: ProfessionalLayoutBox
    text: str = ""
    font_size_pt: float = 18.0
    min_font_size_pt: float = _MIN_BODY_FONT_PT
    evidence_ref: str | None = None
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["box"] = self.box.as_dict()
        return payload


@dataclass(frozen=True)
class ProfessionalLayoutSlideRequest:
    slide_id: str
    role: str
    title: str
    body_items: tuple[str, ...] = ()
    layout_family_hint: str = "title_and_bullets"
    requires_image: bool = False
    requires_chart: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["body_items"] = list(self.body_items)
        return payload


@dataclass(frozen=True)
class ProfessionalLayoutSlidePlan:
    slide_id: str
    role: str
    layout_family: str
    blocks: tuple[ProfessionalLayoutBlock, ...]
    title_clipped: bool
    overlap_count: int
    density_score: float
    contrast_score: float
    readability_score: float
    layout_score: float
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "role": self.role,
            "layout_family": self.layout_family,
            "blocks": [block.as_dict() for block in self.blocks],
            "title_clipped": self.title_clipped,
            "overlap_count": self.overlap_count,
            "density_score": self.density_score,
            "contrast_score": self.contrast_score,
            "readability_score": self.readability_score,
            "layout_score": self.layout_score,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class ProfessionalLayoutResult:
    schema_version: str
    phase: str
    status: ProfessionalLayoutStatus
    professional_layout_engine_implemented: bool
    deterministic_layout_solver_implemented: bool
    grid_layout_implemented: bool
    typographic_scale_implemented: bool
    text_fitting_implemented: bool
    overlap_detection_implemented: bool
    contrast_density_readability_scores_implemented: bool
    title_clipping_prevention_implemented: bool
    slide_size: dict[str, int]
    design_tokens: dict[str, Any]
    slide_count: int
    slide_plans: tuple[ProfessionalLayoutSlidePlan, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    native_pptx_layout_mapping_implemented: bool = False
    renderer_runtime_changed: bool = False
    rendered_png_qa_executed: bool = False
    visual_qa_executed: bool = False
    production_layout_claimed: bool = False
    kimi_level_quality_claimed: bool = False
    ui_changed: bool = False
    gigachat_runtime_changed: bool = False
    docker_deploy_postgres_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "status": self.status,
            "professional_layout_engine_implemented": self.professional_layout_engine_implemented,
            "deterministic_layout_solver_implemented": self.deterministic_layout_solver_implemented,
            "grid_layout_implemented": self.grid_layout_implemented,
            "typographic_scale_implemented": self.typographic_scale_implemented,
            "text_fitting_implemented": self.text_fitting_implemented,
            "overlap_detection_implemented": self.overlap_detection_implemented,
            "contrast_density_readability_scores_implemented": self.contrast_density_readability_scores_implemented,
            "title_clipping_prevention_implemented": self.title_clipping_prevention_implemented,
            "slide_size": dict(self.slide_size),
            "design_tokens": dict(self.design_tokens),
            "slide_count": self.slide_count,
            "slide_plans": [plan.as_dict() for plan in self.slide_plans],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "native_pptx_layout_mapping_implemented": self.native_pptx_layout_mapping_implemented,
            "renderer_runtime_changed": self.renderer_runtime_changed,
            "rendered_png_qa_executed": self.rendered_png_qa_executed,
            "visual_qa_executed": self.visual_qa_executed,
            "production_layout_claimed": self.production_layout_claimed,
            "kimi_level_quality_claimed": self.kimi_level_quality_claimed,
            "ui_changed": self.ui_changed,
            "gigachat_runtime_changed": self.gigachat_runtime_changed,
            "docker_deploy_postgres_changed": self.docker_deploy_postgres_changed,
            "non_goals": [
                "no_renderer_runtime_mapping",
                "no_native_pptx_chart_or_image_placement",
                "no_visual_qa_scoring_runtime",
                "no_rendered_png_qa_execution",
                "no_production_layout_quality_claim",
                "no_kimi_level_quality_claim",
                "no_ui_changes",
                "no_gigachat_runtime_changes",
                "no_docker_deploy_postgres_changes",
            ],
        }


def solve_professional_layout(
    slide_requests: Iterable[ProfessionalLayoutSlideRequest | dict[str, Any]],
    *,
    template_profile: TemplateBrandProfileResult | dict[str, Any] | None = None,
    source_image_selection: SourceImageSelectionResult | dict[str, Any] | None = None,
    data_backed_charts: DataBackedChartResult | dict[str, Any] | None = None,
) -> ProfessionalLayoutResult:
    """Build deterministic slide layout plans and layout-quality scores.

    KR-7L is a planning/constraint layer. It produces boxes, font choices and
    layout scores suitable for later renderer mapping work, but it does not write
    PPTX shapes, render PNG proofs, or claim production layout quality.
    """

    requests = tuple(_coerce_slide_request(request) for request in slide_requests)
    slide_size = _slide_size_from_template(template_profile)
    design_tokens = _design_tokens_from_template(template_profile)
    image_bindings = _image_binding_by_slide(source_image_selection)
    chart_bindings = _chart_binding_by_slide(data_backed_charts)

    plans: list[ProfessionalLayoutSlidePlan] = []
    warnings: list[str] = []
    errors: list[str] = []
    for request in requests:
        plan = _solve_slide(request, slide_size=slide_size, design_tokens=design_tokens, image_binding=image_bindings.get(request.slide_id), chart_binding=chart_bindings.get(request.slide_id))
        plans.append(plan)
        warnings.extend(plan.warnings)
        errors.extend(plan.errors)

    if errors:
        status: ProfessionalLayoutStatus = "blocked"
    elif warnings:
        status = "degraded"
    else:
        status = "ready"

    return ProfessionalLayoutResult(
        schema_version=PROFESSIONAL_LAYOUT_SCHEMA_VERSION,
        phase=PROFESSIONAL_LAYOUT_PHASE,
        status=status,
        professional_layout_engine_implemented=True,
        deterministic_layout_solver_implemented=True,
        grid_layout_implemented=True,
        typographic_scale_implemented=True,
        text_fitting_implemented=True,
        overlap_detection_implemented=True,
        contrast_density_readability_scores_implemented=True,
        title_clipping_prevention_implemented=True,
        slide_size=slide_size,
        design_tokens=design_tokens,
        slide_count=len(plans),
        slide_plans=tuple(plans),
        warnings=tuple(_unique(warnings)),
        errors=tuple(_unique(errors)),
    )


def sample_professional_layout_report() -> dict[str, Any]:
    template_profile = sample_template_brand_profile_report()
    image_selection = sample_source_image_selection_report()
    chart_bindings = sample_data_backed_chart_report()
    requests = (
        ProfessionalLayoutSlideRequest(
            slide_id="s001",
            role="title",
            title="Market evidence dashboard",
            body_items=("Source-backed revenue, margin, and retention signals",),
            layout_family_hint="title_with_visual",
            requires_image=True,
        ),
        ProfessionalLayoutSlideRequest(
            slide_id="s003",
            role="data",
            title="Quarterly revenue data-backed chart",
            body_items=("Revenue increased across Q1-Q4.", "Costs remained controlled."),
            layout_family_hint="data_summary",
            requires_chart=True,
        ),
    )
    return solve_professional_layout(
        requests,
        template_profile=template_profile,
        source_image_selection=image_selection,
        data_backed_charts=chart_bindings,
    ).as_dict()


def _solve_slide(
    request: ProfessionalLayoutSlideRequest,
    *,
    slide_size: dict[str, int],
    design_tokens: dict[str, Any],
    image_binding: dict[str, Any] | SourceImageSlideBinding | None,
    chart_binding: dict[str, Any] | DataChartBinding | None,
) -> ProfessionalLayoutSlidePlan:
    width = int(slide_size["width_emu"])
    height = int(slide_size["height_emu"])
    margin = int(design_tokens["margin_emu"])
    gutter = int(design_tokens["gutter_emu"])
    content_width = width - (2 * margin)
    content_height = height - (2 * margin)
    layout_family = _layout_family(request)
    warnings: list[str] = []
    errors: list[str] = []

    title_height = max(int(height * 0.13), 760_000)
    title_font = _fit_font(request.title, ProfessionalLayoutBox(margin, margin, content_width, title_height), preferred=34.0, minimum=_MIN_TITLE_FONT_PT)
    title_clipped = title_font < _MIN_TITLE_FONT_PT
    if title_clipped:
        errors.append(f"slide {request.slide_id} title cannot fit at minimum title font")

    blocks: list[ProfessionalLayoutBlock] = [
        ProfessionalLayoutBlock(
            block_id=f"{request.slide_id}_title",
            block_type="title",
            role="title",
            status="placed",
            box=ProfessionalLayoutBox(margin, margin, content_width, title_height),
            text=request.title,
            font_size_pt=title_font,
            min_font_size_pt=_MIN_TITLE_FONT_PT,
        )
    ]

    body_text = "\n".join(item.strip() for item in request.body_items if item and item.strip())
    below_title_y = margin + title_height + gutter
    below_title_h = height - below_title_y - margin

    has_selected_image = _binding_selected(image_binding)
    has_bound_chart = _binding_bound(chart_binding)
    if request.requires_image and not has_selected_image:
        warnings.append(f"slide {request.slide_id} uses typographic fallback because no selected source image binding was provided")
    if request.requires_chart and not has_bound_chart:
        warnings.append(f"slide {request.slide_id} uses chart placeholder text because no bound chart data binding was provided")

    if layout_family in {"content_with_visual", "title_with_visual"} and has_selected_image:
        left_w = int((content_width - gutter) * 0.48)
        right_w = content_width - gutter - left_w
        body_box = ProfessionalLayoutBox(margin, below_title_y, left_w, below_title_h)
        visual_box = ProfessionalLayoutBox(margin + left_w + gutter, below_title_y, right_w, below_title_h)
        blocks.append(_body_block(request, body_text, body_box))
        blocks.append(
            ProfessionalLayoutBlock(
                block_id=f"{request.slide_id}_source_image",
                block_type="image",
                role="source_image",
                status="placed",
                box=visual_box,
                evidence_ref=_binding_evidence_ref(image_binding),
                font_size_pt=0.0,
                min_font_size_pt=0.0,
            )
        )
    elif layout_family == "data_summary" and has_bound_chart:
        chart_h = int(below_title_h * 0.58)
        body_h = below_title_h - chart_h - gutter
        chart_box = ProfessionalLayoutBox(margin, below_title_y, content_width, chart_h)
        body_box = ProfessionalLayoutBox(margin, below_title_y + chart_h + gutter, content_width, body_h)
        blocks.append(
            ProfessionalLayoutBlock(
                block_id=f"{request.slide_id}_data_chart",
                block_type="chart",
                role="data_chart_spec",
                status="placed",
                box=chart_box,
                evidence_ref=_binding_evidence_ref(chart_binding),
                font_size_pt=0.0,
                min_font_size_pt=0.0,
            )
        )
        blocks.append(_body_block(request, body_text, body_box))
    elif layout_family == "two_column_comparison":
        left_w = int((content_width - gutter) / 2)
        right_w = content_width - gutter - left_w
        body_chunks = _split_body(body_text)
        blocks.append(_body_block(request, body_chunks[0], ProfessionalLayoutBox(margin, below_title_y, left_w, below_title_h), suffix="left"))
        blocks.append(_body_block(request, body_chunks[1], ProfessionalLayoutBox(margin + left_w + gutter, below_title_y, right_w, below_title_h), suffix="right"))
    else:
        blocks.append(_body_block(request, body_text, ProfessionalLayoutBox(margin, below_title_y, content_width, below_title_h)))

    overlap_count = _overlap_count(tuple(blocks))
    if overlap_count:
        errors.append(f"slide {request.slide_id} has overlapping layout blocks")
    if any(not _inside_slide(block.box, width=width, height=height) for block in blocks):
        errors.append(f"slide {request.slide_id} has layout blocks outside slide bounds")

    density = _density_score(tuple(blocks), slide_area=width * height)
    if density > _MAX_DENSITY:
        warnings.append(f"slide {request.slide_id} density score is above recommended maximum")
    contrast = _contrast_score(design_tokens)
    readability = _readability_score(tuple(blocks), density=density)
    layout_score = round(max(0.0, min(1.0, (1.0 - min(density, 1.0)) * 0.35 + contrast * 0.30 + readability * 0.35 - overlap_count * 0.25)), 3)

    return ProfessionalLayoutSlidePlan(
        slide_id=request.slide_id,
        role=request.role,
        layout_family=layout_family,
        blocks=tuple(blocks),
        title_clipped=title_clipped,
        overlap_count=overlap_count,
        density_score=round(density, 3),
        contrast_score=round(contrast, 3),
        readability_score=round(readability, 3),
        layout_score=layout_score,
        warnings=tuple(_unique(warnings)),
        errors=tuple(_unique(errors)),
    )


def _body_block(request: ProfessionalLayoutSlideRequest, body_text: str, box: ProfessionalLayoutBox, *, suffix: str = "body") -> ProfessionalLayoutBlock:
    text = body_text or ""
    font_size = _fit_font(text, box, preferred=19.0, minimum=_MIN_BODY_FONT_PT)
    return ProfessionalLayoutBlock(
        block_id=f"{request.slide_id}_{suffix}",
        block_type="body",
        role="body",
        status="placed" if text else "typographic_fallback",
        box=box,
        text=text,
        font_size_pt=font_size,
        min_font_size_pt=_MIN_BODY_FONT_PT,
        fallback_reason=None if text else "no_body_text_supplied",
    )


def _coerce_slide_request(value: ProfessionalLayoutSlideRequest | dict[str, Any]) -> ProfessionalLayoutSlideRequest:
    if isinstance(value, ProfessionalLayoutSlideRequest):
        return value
    return ProfessionalLayoutSlideRequest(
        slide_id=str(value.get("slide_id") or "slide"),
        role=str(value.get("role") or "content"),
        title=str(value.get("title") or "Untitled slide"),
        body_items=tuple(str(item) for item in value.get("body_items", ()) if str(item).strip()),
        layout_family_hint=str(value.get("layout_family_hint") or value.get("layout_family") or "title_and_bullets"),
        requires_image=bool(value.get("requires_image", False)),
        requires_chart=bool(value.get("requires_chart", False)),
    )


def _layout_family(request: ProfessionalLayoutSlideRequest) -> str:
    family = (request.layout_family_hint or "title_and_bullets").strip().lower()
    allowed = {"title_slide", "section_slide", "title_and_bullets", "two_column_comparison", "timeline", "data_summary", "conclusion", "content_with_visual", "title_with_visual"}
    if request.requires_chart:
        return "data_summary"
    if request.requires_image and family not in {"content_with_visual", "title_with_visual"}:
        return "content_with_visual"
    return family if family in allowed else "title_and_bullets"


def _slide_size_from_template(template_profile: TemplateBrandProfileResult | dict[str, Any] | None) -> dict[str, int]:
    payload = template_profile.as_dict() if hasattr(template_profile, "as_dict") else dict(template_profile or {})
    slide_size = payload.get("slide_size") or {}
    width = int(slide_size.get("width_emu") or DEFAULT_SLIDE_WIDTH_EMU)
    height = int(slide_size.get("height_emu") or DEFAULT_SLIDE_HEIGHT_EMU)
    return {"width_emu": width, "height_emu": height}


def _design_tokens_from_template(template_profile: TemplateBrandProfileResult | dict[str, Any] | None) -> dict[str, Any]:
    payload = template_profile.as_dict() if hasattr(template_profile, "as_dict") else dict(template_profile or {})
    theme = payload.get("theme") or {}
    colors = theme.get("color_tokens") or {}
    return {
        "margin_emu": _DEFAULT_MARGIN_EMU,
        "gutter_emu": _DEFAULT_GUTTER_EMU,
        "grid_columns": _GRID_COLUMNS,
        "grid_rows": _GRID_ROWS,
        "title_font_pt": 34.0,
        "body_font_pt": 19.0,
        "major_font": theme.get("major_font") or "Aptos Display",
        "minor_font": theme.get("minor_font") or "Aptos",
        "background_color": colors.get("background1") or "FFFFFF",
        "text_color": colors.get("text1") or "111111",
        "accent_color": colors.get("accent1") or "4472C4",
    }


def _image_binding_by_slide(value: SourceImageSelectionResult | dict[str, Any] | None) -> dict[str, Any]:
    payload = value.as_dict() if hasattr(value, "as_dict") else dict(value or {})
    return {str(binding.get("slide_id")): binding for binding in payload.get("slide_bindings", ()) if isinstance(binding, dict)}


def _chart_binding_by_slide(value: DataBackedChartResult | dict[str, Any] | None) -> dict[str, Any]:
    payload = value.as_dict() if hasattr(value, "as_dict") else dict(value or {})
    return {str(binding.get("slide_id")): binding for binding in payload.get("chart_bindings", ()) if isinstance(binding, dict)}


def _binding_selected(binding: dict[str, Any] | SourceImageSlideBinding | None) -> bool:
    payload = binding.as_dict() if hasattr(binding, "as_dict") else dict(binding or {})
    return payload.get("status") == "selected" and bool(payload.get("selected_image_id"))


def _binding_bound(binding: dict[str, Any] | DataChartBinding | None) -> bool:
    payload = binding.as_dict() if hasattr(binding, "as_dict") else dict(binding or {})
    return payload.get("status") == "bound" and bool(payload.get("data_ref"))


def _binding_evidence_ref(binding: dict[str, Any] | Any | None) -> str | None:
    payload = binding.as_dict() if hasattr(binding, "as_dict") else dict(binding or {})
    return payload.get("provenance_ref") or payload.get("citation") or payload.get("data_ref")


def _fit_font(text: str, box: ProfessionalLayoutBox, *, preferred: float, minimum: float) -> float:
    text = text or ""
    if not text.strip():
        return preferred
    words = max(1, len(_TOKEN_RE.findall(text)))
    # Approximate text capacity using line height and average character width.
    for size in (preferred, 30.0, 26.0, 22.0, 19.0, 17.0, 15.0, minimum):
        char_w = size * 0.52 * (EMU_PER_INCH / 72)
        line_h = size * 1.18 * (EMU_PER_INCH / 72)
        chars_per_line = max(8, int(box.cx / max(char_w, 1)))
        lines = max(1, math.ceil(max(len(text), words * 5) / chars_per_line))
        if lines * line_h <= box.cy:
            return round(size, 1)
    return round(minimum - 1.0, 1)


def _split_body(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    midpoint = max(1, math.ceil(len(lines) / 2))
    return "\n".join(lines[:midpoint]), "\n".join(lines[midpoint:])


def _overlap_count(blocks: tuple[ProfessionalLayoutBlock, ...]) -> int:
    count = 0
    for idx, left in enumerate(blocks):
        for right in blocks[idx + 1 :]:
            if _boxes_overlap(left.box, right.box):
                count += 1
    return count


def _boxes_overlap(left: ProfessionalLayoutBox, right: ProfessionalLayoutBox) -> bool:
    if left.area == 0 or right.area == 0:
        return False
    return left.x < right.right and left.right > right.x and left.y < right.bottom and left.bottom > right.y


def _inside_slide(box: ProfessionalLayoutBox, *, width: int, height: int) -> bool:
    return box.x >= 0 and box.y >= 0 and box.right <= width and box.bottom <= height and box.cx > 0 and box.cy > 0


def _density_score(blocks: tuple[ProfessionalLayoutBlock, ...], *, slide_area: int) -> float:
    occupied = sum(block.box.area for block in blocks if block.status == "placed")
    return max(0.0, min(1.0, occupied / max(slide_area, 1)))


def _contrast_score(tokens: dict[str, Any]) -> float:
    fg = _hex_to_rgb(str(tokens.get("text_color") or "111111"))
    bg = _hex_to_rgb(str(tokens.get("background_color") or "FFFFFF"))
    ratio = _contrast_ratio(fg, bg)
    return max(0.0, min(1.0, (ratio - 1.0) / 6.0))


def _readability_score(blocks: tuple[ProfessionalLayoutBlock, ...], *, density: float) -> float:
    penalties = 0.0
    for block in blocks:
        if block.block_type == "title" and block.font_size_pt < _MIN_TITLE_FONT_PT:
            penalties += 0.35
        if block.block_type == "body" and block.text and block.font_size_pt < _MIN_BODY_FONT_PT:
            penalties += 0.25
    if density > _MAX_DENSITY:
        penalties += min(0.35, density - _MAX_DENSITY)
    return max(0.0, min(1.0, 1.0 - penalties))


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return (1.0, 1.0, 1.0)
    try:
        return tuple(int(value[idx : idx + 2], 16) / 255.0 for idx in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return (1.0, 1.0, 1.0)


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    def channel(value: float) -> float:
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(item) for item in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    l1 = _relative_luminance(left)
    l2 = _relative_luminance(right)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
