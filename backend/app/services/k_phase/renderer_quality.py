from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from typing import Any

from backend.app.services.slides_service.blocks import (
    BulletBlock,
    BusinessMetricBlock,
    ChartBlock,
    ComparisonBlock,
    SlideBlock,
    TableBlock,
    TimelineBlock,
)
from backend.app.services.slides_service.image_pipeline import VisualIntent
from backend.app.services.slides_service.layouts import get_template_registry
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType

K3_CHECKPOINT = "K3"
K3_SCHEMA_VERSION = "k3.renderer_quality_runtime.v1"
K_PHASE_BRANCH = "8_K_Phase"
K3_BASE_AFTER_K2 = "48f8579adc9be176ce60cc1fa39fe5ad0b19f3a4"
LOCAL_THEME_SOURCE = "local_builtin_registry"
DEFAULT_LOCAL_TEMPLATE_ID = "business_clean"
_ALLOWED_RENDER_MODES = {"adaptive", "template"}


@dataclass(frozen=True)
class ContentDensityPolicy:
    max_title_chars: int = 72
    max_bullets_per_slide: int = 4
    max_words_per_bullet: int = 14
    max_body_chars: int = 360
    max_table_rows: int = 5
    max_table_columns: int = 4
    max_chart_categories: int = 6
    max_comparison_items_per_side: int = 4
    max_timeline_items: int = 5

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class LayoutSelectionPolicy:
    policy_id: str = "k3.deterministic_layout_selection.v1"
    title_layout: str = "title_with_visual"
    section_layout: str = "section_slide"
    content_layout: str = "content_with_visual"
    comparison_layout: str = "two_column_comparison"
    timeline_layout: str = "timeline"
    data_layout: str = "data_summary"
    conclusion_layout: str = "conclusion"
    appendix_layout: str = "section_slide"
    fallback_layout: str = "title_and_bullets"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class VisualHierarchyPolicy:
    policy_id: str = "k3.visual_hierarchy.v1"
    title_role: str = "single_slide_message"
    subtitle_role: str = "optional_contextual_qualifier"
    body_role: str = "bounded_supporting_evidence"
    emphasis_rule: str = "prefer_fewer_high-signal_shapes_over_dense_text"
    title_subtitle_body_balance: str = "title_first_bounded_body"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class LocalThemePack:
    template_id: str
    display_name: str
    source: str = LOCAL_THEME_SOURCE
    network_required: bool = False
    external_download_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RenderQualityProfile:
    profile_id: str = "k3_local_deterministic_quality_profile"
    render_mode: str = "adaptive"
    template_id: str = DEFAULT_LOCAL_TEMPLATE_ID
    density_policy: ContentDensityPolicy = ContentDensityPolicy()
    layout_policy: LayoutSelectionPolicy = LayoutSelectionPolicy()
    hierarchy_policy: VisualHierarchyPolicy = VisualHierarchyPolicy()

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "render_mode": self.render_mode,
            "template_id": self.template_id,
            "density_policy": self.density_policy.as_dict(),
            "layout_policy": self.layout_policy.as_dict(),
            "hierarchy_policy": self.hierarchy_policy.as_dict(),
        }


@dataclass(frozen=True)
class OverflowRiskAssessment:
    slide_id: str
    bullet_count: int
    body_chars: int
    block_count: int
    table_rows_max: int
    table_columns_max: int
    chart_categories_max: int
    risk_level: str
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RendererQualitySlideResult:
    slide_id: str
    slide_type: str
    selected_layout_hint: str
    visual_hierarchy: str
    density_level_before: str
    density_level_after: str
    overflow_risk_before: str
    overflow_risk_after: str
    overflow_prevention_applied: bool
    table_chart_quality_supported: bool
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RendererQualityResult:
    original_plan_digest: str
    render_plan: PresentationPlan
    profile: RenderQualityProfile
    local_theme_pack: LocalThemePack
    slide_results: tuple[RendererQualitySlideResult, ...]
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "original_plan_digest": self.original_plan_digest,
            "render_plan_slide_count": len(self.render_plan.slides),
            "profile": self.profile.as_dict(),
            "local_theme_pack": self.local_theme_pack.as_dict(),
            "slide_results": [item.as_dict() for item in self.slide_results],
            "safe_metadata": dict(self.safe_metadata),
        }


def build_default_k3_quality_profile(*, render_mode: str = "adaptive", template_id: str = DEFAULT_LOCAL_TEMPLATE_ID) -> RenderQualityProfile:
    _validate_profile(render_mode=render_mode, template_id=template_id)
    return RenderQualityProfile(render_mode=render_mode, template_id=template_id)


def improve_presentation_plan_render_quality(
    plan: PresentationPlan,
    *,
    profile: RenderQualityProfile | None = None,
) -> RendererQualityResult:
    """Build a deterministic render-quality pass over an approved PresentationPlan.

    K3 is intentionally local and bounded: it selects existing layout hints,
    reduces density and overflow risk, normalizes table/chart blocks, and emits
    safe render-quality metadata. It does not add a public API, a schema
    migration, cloud calls, visual QA runtime, or Kimi-level claims.
    """

    if not plan.slides:
        raise ValueError("K3 renderer quality runtime requires at least one planned slide.")
    profile = profile or build_default_k3_quality_profile()
    _validate_profile(render_mode=profile.render_mode, template_id=profile.template_id)
    theme_pack = _resolve_local_theme_pack(profile.template_id)

    improved_slides: list[PlannedSlide] = []
    slide_results: list[RendererQualitySlideResult] = []
    overflow_prevention_count = 0
    table_chart_slide_count = 0

    for slide in plan.slides:
        before = assess_overflow_risk(slide, profile.density_policy)
        layout_hint = select_layout_hint(slide, profile.layout_policy)
        improved_slide = _normalize_slide_for_render_quality(slide, layout_hint=layout_hint, density_policy=profile.density_policy)
        after = assess_overflow_risk(improved_slide, profile.density_policy)
        applied = before.risk_level != "low" or _slide_digest(slide) != _slide_digest(improved_slide)
        if applied:
            overflow_prevention_count += 1
        table_chart_supported = _has_table_or_chart(slide)
        if table_chart_supported:
            table_chart_slide_count += 1
        slide_results.append(
            RendererQualitySlideResult(
                slide_id=slide.slide_id,
                slide_type=slide.slide_type.value,
                selected_layout_hint=layout_hint,
                visual_hierarchy=profile.hierarchy_policy.title_subtitle_body_balance,
                density_level_before=_density_level(before),
                density_level_after=_density_level(after),
                overflow_risk_before=before.risk_level,
                overflow_risk_after=after.risk_level,
                overflow_prevention_applied=applied,
                table_chart_quality_supported=table_chart_supported,
                warnings=after.warnings,
            )
        )
        improved_slides.append(improved_slide)

    render_plan = PresentationPlan(
        deck_title=_trim_words(plan.deck_title, max_chars=profile.density_policy.max_title_chars),
        deck_goal=plan.deck_goal,
        audience=plan.audience,
        tone=plan.tone,
        target_slide_count=len(improved_slides),
        story_arc=tuple(slide.story_arc_stage for slide in improved_slides),
        slides=tuple(improved_slides),
    )
    safe_metadata = _safe_metadata(
        plan=plan,
        render_plan=render_plan,
        profile=profile,
        theme_pack=theme_pack,
        slide_results=tuple(slide_results),
        overflow_prevention_count=overflow_prevention_count,
        table_chart_slide_count=table_chart_slide_count,
    )
    return RendererQualityResult(
        original_plan_digest=_plan_digest(plan),
        render_plan=render_plan,
        profile=profile,
        local_theme_pack=theme_pack,
        slide_results=tuple(slide_results),
        safe_metadata=safe_metadata,
    )


def assess_overflow_risk(slide: PlannedSlide, density_policy: ContentDensityPolicy | None = None) -> OverflowRiskAssessment:
    policy = density_policy or ContentDensityPolicy()
    bullet_count = len(slide.bullets)
    body_chars = sum(len(item) for item in slide.bullets)
    block_count = len(slide.blocks)
    table_rows_max = 0
    table_columns_max = 0
    chart_categories_max = 0
    warnings: list[str] = []

    if len(slide.title) > policy.max_title_chars:
        warnings.append("title_exceeds_policy")
    if bullet_count > policy.max_bullets_per_slide:
        warnings.append("too_many_bullets")
    if body_chars > policy.max_body_chars:
        warnings.append("body_too_dense")

    for block in slide.blocks:
        if isinstance(block, TableBlock):
            table_rows_max = max(table_rows_max, len(block.rows))
            table_columns_max = max(table_columns_max, len(block.columns))
            if len(block.rows) > policy.max_table_rows:
                warnings.append("table_rows_exceed_policy")
            if len(block.columns) > policy.max_table_columns:
                warnings.append("table_columns_exceed_policy")
        elif isinstance(block, ChartBlock):
            chart_categories_max = max(chart_categories_max, len(block.categories))
            if len(block.categories) > policy.max_chart_categories:
                warnings.append("chart_categories_exceed_policy")
        elif isinstance(block, ComparisonBlock):
            if len(block.left_items) > policy.max_comparison_items_per_side or len(block.right_items) > policy.max_comparison_items_per_side:
                warnings.append("comparison_items_exceed_policy")
        elif isinstance(block, TimelineBlock):
            if len(block.items) > policy.max_timeline_items:
                warnings.append("timeline_items_exceed_policy")
        elif isinstance(block, BulletBlock):
            if len(block.bullets) > policy.max_bullets_per_slide:
                warnings.append("block_bullets_exceed_policy")

    risk_level = "low"
    if warnings:
        risk_level = "medium"
    if body_chars > policy.max_body_chars * 1.35 or bullet_count > policy.max_bullets_per_slide + 2:
        risk_level = "high"
    if table_rows_max > policy.max_table_rows + 2 or table_columns_max > policy.max_table_columns + 1:
        risk_level = "high"
    if chart_categories_max > policy.max_chart_categories + 2:
        risk_level = "high"

    return OverflowRiskAssessment(
        slide_id=slide.slide_id,
        bullet_count=bullet_count,
        body_chars=body_chars,
        block_count=block_count,
        table_rows_max=table_rows_max,
        table_columns_max=table_columns_max,
        chart_categories_max=chart_categories_max,
        risk_level=risk_level,
        warnings=tuple(sorted(set(warnings))),
    )


def select_layout_hint(slide: PlannedSlide, layout_policy: LayoutSelectionPolicy | None = None) -> str:
    policy = layout_policy or LayoutSelectionPolicy()
    if any(isinstance(block, ComparisonBlock) for block in slide.blocks):
        return policy.comparison_layout
    if any(isinstance(block, TimelineBlock) for block in slide.blocks):
        return policy.timeline_layout
    if any(isinstance(block, (TableBlock, ChartBlock, BusinessMetricBlock)) for block in slide.blocks):
        return policy.data_layout
    if slide.slide_type is SlideType.TITLE:
        return policy.title_layout if slide.visual_intent is not VisualIntent.NONE else "title_slide"
    if slide.slide_type is SlideType.SECTION:
        return policy.section_layout
    if slide.slide_type is SlideType.COMPARISON:
        return policy.comparison_layout
    if slide.slide_type is SlideType.TIMELINE:
        return policy.timeline_layout
    if slide.slide_type is SlideType.DATA:
        return policy.data_layout
    if slide.slide_type is SlideType.CONCLUSION:
        return policy.conclusion_layout
    if slide.slide_type is SlideType.APPENDIX:
        return policy.appendix_layout
    if slide.visual_intent is not VisualIntent.NONE:
        return policy.content_layout
    return slide.layout_hint or policy.fallback_layout


def build_k3_capabilities_report() -> dict[str, object]:
    return {
        "mode": "k3-renderer-quality-runtime",
        "checkpoint": K3_CHECKPOINT,
        "schema_version": K3_SCHEMA_VERSION,
        "k3_base_after_k2": K3_BASE_AFTER_K2,
        "renderer_quality_runtime_supported": True,
        "layout_selection_engine_supported": True,
        "content_density_control_supported": True,
        "visual_hierarchy_supported": True,
        "table_chart_rendering_quality_supported": True,
        "title_subtitle_body_balance_supported": True,
        "local_theme_pack_supported": True,
        "overflow_prevention_supported": True,
        "deterministic_rendering_quality_metadata_supported": True,
        "safe_acceptance_checker_supported": True,
        "network_required": False,
        "cloud_llm_added_by_k3": False,
        "api_endpoint_added_by_k3": False,
        "db_schema_migration_added_by_k3": False,
        "frontend_runtime_changed_by_k3": False,
        "dependency_versions_changed_by_k3": False,
        "dockerfiles_changed_by_k3": False,
        "visual_qa_runtime_added_by_k3": False,
        "source_to_slide_provenance_added_by_k3": False,
        "kimi_level_claimed_by_k3": False,
        "whole_project_kimi_level_supported": False,
    }


def _normalize_slide_for_render_quality(slide: PlannedSlide, *, layout_hint: str, density_policy: ContentDensityPolicy) -> PlannedSlide:
    title = _trim_words(slide.title, max_chars=density_policy.max_title_chars)
    bullets = tuple(
        _trim_words(bullet, max_words=density_policy.max_words_per_bullet, max_chars=120)
        for bullet in slide.bullets[: density_policy.max_bullets_per_slide]
        if bullet.strip()
    ) or ("No supporting detail provided",)
    blocks = _normalize_blocks(slide.blocks, density_policy=density_policy)
    speaker_notes = slide.speaker_notes or ""
    if assess_overflow_risk(slide, density_policy).risk_level != "low":
        marker = "K3 renderer quality: density bounded for deterministic local rendering."
        speaker_notes = f"{speaker_notes}\n{marker}".strip()
    return replace(slide, title=title, bullets=bullets, blocks=blocks, layout_hint=layout_hint, speaker_notes=speaker_notes)


def _normalize_blocks(blocks: tuple[SlideBlock, ...], *, density_policy: ContentDensityPolicy) -> tuple[SlideBlock, ...]:
    normalized: list[SlideBlock] = []
    for block in blocks:
        if isinstance(block, TableBlock):
            columns = block.columns[: density_policy.max_table_columns]
            rows = tuple(tuple(row[: len(columns)]) for row in block.rows[: density_policy.max_table_rows])
            normalized.append(replace(block, columns=columns, rows=rows))
        elif isinstance(block, ChartBlock):
            limit = density_policy.max_chart_categories
            normalized.append(replace(block, categories=block.categories[:limit], values=block.values[:limit]))
        elif isinstance(block, ComparisonBlock):
            normalized.append(
                replace(
                    block,
                    left_items=block.left_items[: density_policy.max_comparison_items_per_side],
                    right_items=block.right_items[: density_policy.max_comparison_items_per_side],
                )
            )
        elif isinstance(block, TimelineBlock):
            normalized.append(replace(block, items=block.items[: density_policy.max_timeline_items]))
        elif isinstance(block, BusinessMetricBlock):
            normalized.append(replace(block, metrics=block.metrics[:4]))
        elif isinstance(block, BulletBlock):
            bullets = tuple(
                _trim_words(item, max_words=density_policy.max_words_per_bullet, max_chars=120)
                for item in block.bullets[: density_policy.max_bullets_per_slide]
            )
            normalized.append(replace(block, bullets=bullets))
        else:
            normalized.append(block)
    return tuple(normalized)


def _resolve_local_theme_pack(template_id: str) -> LocalThemePack:
    registry = get_template_registry()
    if template_id not in registry:
        allowed = ", ".join(sorted(registry))
        raise ValueError(f"Unsupported K3 local template_id: {template_id!r}. Allowed local template ids: {allowed}")
    template = registry[template_id]
    return LocalThemePack(template_id=template.template_id, display_name=template.display_name)


def _validate_profile(*, render_mode: str, template_id: str) -> None:
    if render_mode not in _ALLOWED_RENDER_MODES:
        raise ValueError(f"Unsupported K3 render mode: {render_mode!r}")
    if not template_id.strip():
        raise ValueError("K3 renderer quality runtime requires a local template_id.")
    lowered = template_id.strip().lower()
    if "://" in lowered or "/" in template_id or "\\" in template_id or ".." in template_id:
        raise ValueError("K3 renderer quality runtime accepts only bundled local template ids.")


def _safe_metadata(
    *,
    plan: PresentationPlan,
    render_plan: PresentationPlan,
    profile: RenderQualityProfile,
    theme_pack: LocalThemePack,
    slide_results: tuple[RendererQualitySlideResult, ...],
    overflow_prevention_count: int,
    table_chart_slide_count: int,
) -> dict[str, object]:
    metadata = {
        **build_k3_capabilities_report(),
        "profile_id": profile.profile_id,
        "render_mode": profile.render_mode,
        "template_id": theme_pack.template_id,
        "template_source": theme_pack.source,
        "original_plan_digest": _plan_digest(plan),
        "render_plan_digest": _plan_digest(render_plan),
        "slide_count": len(render_plan.slides),
        "overflow_prevention_count": overflow_prevention_count,
        "table_chart_slide_count": table_chart_slide_count,
        "slide_layout_hints": tuple(result.selected_layout_hint for result in slide_results),
        "slide_overflow_risk_after": tuple(result.overflow_risk_after for result in slide_results),
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "raw_sensitive_values_stored": False,
    }
    json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    return metadata


def _density_level(assessment: OverflowRiskAssessment) -> str:
    if assessment.risk_level == "high":
        return "overloaded"
    if assessment.risk_level == "medium":
        return "dense"
    return "balanced"


def _has_table_or_chart(slide: PlannedSlide) -> bool:
    return any(isinstance(block, (TableBlock, ChartBlock, BusinessMetricBlock)) for block in slide.blocks)


def _trim_words(value: str, *, max_words: int | None = None, max_chars: int) -> str:
    cleaned = " ".join(str(value).replace("\n", " ").split())
    if max_words is not None:
        cleaned = " ".join(cleaned.split()[:max_words])
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max(1, max_chars - 1)].rstrip() + "…"


def _plan_digest(plan: PresentationPlan) -> str:
    payload = {
        "deck_title": plan.deck_title,
        "deck_goal": plan.deck_goal,
        "audience": plan.audience,
        "tone": plan.tone,
        "target_slide_count": plan.target_slide_count,
        "slides": [
            {
                "slide_id": slide.slide_id,
                "slide_type": slide.slide_type.value,
                "story_arc_stage": slide.story_arc_stage.value,
                "title": slide.title,
                "bullets": list(slide.bullets),
                "layout_hint": slide.layout_hint,
                "block_count": len(slide.blocks),
            }
            for slide in plan.slides
        ],
    }
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _slide_digest(slide: PlannedSlide) -> str:
    return sha256(
        json.dumps(
            {
                "title": slide.title,
                "bullets": list(slide.bullets),
                "layout_hint": slide.layout_hint,
                "blocks": [type(block).__name__ for block in slide.blocks],
                "speaker_notes": slide.speaker_notes,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
