from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.app.services.slides_service.blocks import (
    BulletBlock,
    BusinessMetric,
    BusinessMetricBlock,
    ChartBlock,
    ComparisonBlock,
    SlideBlock,
    TableBlock,
    TextBlock,
    TimelineBlock,
    TimelineItem,
)
from backend.app.services.slides_service.image_pipeline import ImageSpec, VisualIntent
from backend.app.services.slides_service.media import SlideMediaAsset


class SlideType(str, Enum):
    TITLE = "title"
    SECTION = "section"
    CONTENT = "content"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    DATA = "data"
    CONCLUSION = "conclusion"
    APPENDIX = "appendix"


class StoryArcStage(str, Enum):
    OPENING = "opening"
    CONTEXT = "context"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    CLOSE = "close"


@dataclass(frozen=True)
class PlannedSlide:
    slide_id: str
    slide_type: SlideType
    story_arc_stage: StoryArcStage
    title: str
    bullets: tuple[str, ...]
    speaker_notes: str | None = None
    layout_hint: str | None = None
    visual_intent: VisualIntent = VisualIntent.NONE
    image_specs: tuple[ImageSpec, ...] = ()
    media_assets: tuple[SlideMediaAsset, ...] = ()
    blocks: tuple[SlideBlock, ...] = ()
    citations: tuple[object, ...] = ()
    source_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresentationPlan:
    deck_title: str
    deck_goal: str
    audience: str
    tone: str
    target_slide_count: int
    story_arc: tuple[StoryArcStage, ...]
    slides: tuple[PlannedSlide, ...]


@dataclass(frozen=True)
class SlideOutlineItem:
    title: str
    bullets: tuple[str, ...]


_BODY_SEQUENCE: tuple[SlideType, ...] = (
    SlideType.CONTENT,
    SlideType.COMPARISON,
    SlideType.TIMELINE,
    SlideType.DATA,
)

_MAX_BULLET_WORDS = 12
_MAX_BULLETS_PER_SLIDE = 3


def build_presentation_plan(
    source_text: str,
    *,
    min_slides: int = 5,
    max_slides: int = 10,
) -> PresentationPlan:
    segments = _extract_segments(source_text)
    target_slide_count = max(min_slides, min(max_slides, len(segments)))

    content_segments = list(segments)
    while len(content_segments) < target_slide_count:
        content_segments.append(f"Additional insight {len(content_segments) + 1}")

    planned_slides: list[PlannedSlide] = []
    reserve_appendix = target_slide_count >= 8

    for index in range(target_slide_count):
        slide_number = index + 1
        slide_id = f"slide_{slide_number:03d}"
        segment = content_segments[index]
        if index == 0:
            slide_type = SlideType.TITLE
            stage = StoryArcStage.OPENING
        elif index == 1:
            slide_type = SlideType.SECTION
            stage = StoryArcStage.CONTEXT
        elif reserve_appendix and index == target_slide_count - 2:
            slide_type = SlideType.APPENDIX
            stage = StoryArcStage.CLOSE
        elif index == target_slide_count - 1:
            slide_type = SlideType.CONCLUSION
            stage = StoryArcStage.CLOSE
        else:
            slide_type = _BODY_SEQUENCE[(index - 2) % len(_BODY_SEQUENCE)]
            stage = (
                StoryArcStage.ANALYSIS
                if slide_type in {SlideType.CONTENT, SlideType.DATA}
                else StoryArcStage.RECOMMENDATION
            )

        title = _plan_title_for_type(slide_type=slide_type, seed=segment)
        bullets = tuple(_bounded_bullets(segment))
        layout_hint = _layout_hint_for_type(slide_type)
        visual_intent = _visual_intent_for_slide(slide_type=slide_type)
        image_specs = _image_specs_for_slide(
            slide_id=slide_id,
            visual_intent=visual_intent,
            title=title,
            bullets=bullets,
        )
        blocks = _structured_blocks_for_slide(slide_id=slide_id, slide_type=slide_type, title=title, bullets=bullets)

        planned_slides.append(
            PlannedSlide(
                slide_id=slide_id,
                slide_type=slide_type,
                story_arc_stage=stage,
                title=title,
                bullets=bullets,
                speaker_notes=_speaker_notes_for_type(slide_type),
                layout_hint=layout_hint,
                visual_intent=visual_intent,
                image_specs=image_specs,
                blocks=blocks,
            )
        )

    slides = tuple(planned_slides)
    return PresentationPlan(
        deck_title=slides[0].title,
        deck_goal="Communicate a concise, bounded slide story from the supplied source text.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=target_slide_count,
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


def plan_to_outline(plan: PresentationPlan) -> tuple[SlideOutlineItem, ...]:
    return tuple(
        SlideOutlineItem(title=f"Slide {index}: {slide.title[:36]}".strip(), bullets=slide.bullets)
        for index, slide in enumerate(plan.slides, start=1)
    )


def build_slides_outline(source_text: str, *, min_slides: int = 5, max_slides: int = 10) -> tuple[SlideOutlineItem, ...]:
    plan = build_presentation_plan(source_text, min_slides=min_slides, max_slides=max_slides)
    return plan_to_outline(plan)


def _extract_segments(source_text: str) -> tuple[str, ...]:
    normalized = source_text.replace("\n", ". ")
    segments = tuple(segment.strip() for segment in normalized.split(".") if segment.strip())
    if segments:
        return segments
    return ("Untitled presentation",)


def _bounded_bullets(text: str) -> list[str]:
    words = [word for word in text.replace("\n", " ").split() if word]
    if not words:
        return ["No supporting detail provided"]

    bullets: list[str] = []
    for start in range(0, min(len(words), _MAX_BULLET_WORDS * _MAX_BULLETS_PER_SLIDE), _MAX_BULLET_WORDS):
        chunk = words[start : start + _MAX_BULLET_WORDS]
        if not chunk:
            continue
        bullets.append(" ".join(chunk).strip())
        if len(bullets) >= _MAX_BULLETS_PER_SLIDE:
            break
    return bullets or ["No supporting detail provided"]


def _plan_title_for_type(*, slide_type: SlideType, seed: str) -> str:
    if slide_type is SlideType.TITLE:
        return seed[:48] or "Untitled Presentation"
    if slide_type is SlideType.SECTION:
        return f"Overview: {seed[:32]}".strip()
    if slide_type is SlideType.COMPARISON:
        return f"Compare: {seed[:32]}".strip()
    if slide_type is SlideType.TIMELINE:
        return f"Timeline: {seed[:32]}".strip()
    if slide_type is SlideType.DATA:
        return f"Data: {seed[:32]}".strip()
    if slide_type is SlideType.CONCLUSION:
        return f"Conclusion: {seed[:32]}".strip()
    if slide_type is SlideType.APPENDIX:
        return f"Appendix: {seed[:32]}".strip()
    return seed[:48] or "Content"


def _speaker_notes_for_type(slide_type: SlideType) -> str:
    if slide_type is SlideType.COMPARISON:
        return "Explain the trade-offs and decision criteria clearly."
    if slide_type is SlideType.TIMELINE:
        return "Walk through sequence and timing without overloading the audience."
    if slide_type is SlideType.DATA:
        return "Highlight only the metrics that support the recommendation."
    return "Expand the key point with concise supporting context."


def _layout_hint_for_type(slide_type: SlideType) -> str:
    if slide_type is SlideType.TITLE:
        return "title_with_visual"
    if slide_type in {SlideType.SECTION, SlideType.APPENDIX}:
        return "section_slide"
    if slide_type is SlideType.CONTENT:
        return "content_with_visual"
    if slide_type is SlideType.COMPARISON:
        return "two_column_comparison"
    if slide_type is SlideType.TIMELINE:
        return "timeline"
    if slide_type is SlideType.DATA:
        return "data_summary"
    if slide_type is SlideType.CONCLUSION:
        return "conclusion"
    return "title_and_bullets"


def _visual_intent_for_slide(*, slide_type: SlideType) -> VisualIntent:
    if slide_type is SlideType.TITLE:
        return VisualIntent.COVER_ILLUSTRATION
    if slide_type is SlideType.CONTENT:
        return VisualIntent.PROCESS_VISUAL
    return VisualIntent.NONE


def _image_specs_for_slide(*, slide_id: str, visual_intent: VisualIntent, title: str, bullets: tuple[str, ...]) -> tuple[ImageSpec, ...]:
    if visual_intent is VisualIntent.NONE:
        return ()
    prompt_parts = [title, *bullets]
    prompt = ". ".join(part for part in prompt_parts if part).strip()
    return (
        ImageSpec(
            spec_id=f"{slide_id}_{visual_intent.value}",
            intent=visual_intent,
            prompt=prompt,
            aspect_ratio="16:9",
            caption=title,
            source_label="Local deterministic slide image generation",
            required=True,
        ),
    )


def _structured_blocks_for_slide(*, slide_id: str, slide_type: SlideType, title: str, bullets: tuple[str, ...]) -> tuple[SlideBlock, ...]:
    if slide_type is SlideType.TITLE:
        return (TextBlock(block_id=f"{slide_id}_text", text=" / ".join(bullets), caption=title),)
    if slide_type is SlideType.COMPARISON:
        left_items, right_items = _split_items_for_comparison(bullets)
        return (
            ComparisonBlock(
                block_id=f"{slide_id}_comparison",
                left_title="Option A / Current path",
                left_items=left_items,
                right_title="Option B / Recommended path",
                right_items=right_items,
            ),
        )
    if slide_type is SlideType.TIMELINE:
        return (TimelineBlock(block_id=f"{slide_id}_timeline", items=_timeline_items_from_bullets(bullets), caption=title),)
    if slide_type is SlideType.DATA:
        return (
            BusinessMetricBlock(block_id=f"{slide_id}_metrics", metrics=_business_metrics_from_bullets(bullets), caption="Business signals"),
            TableBlock(
                block_id=f"{slide_id}_table",
                columns=("Signal", "Evidence", "Weight"),
                rows=_table_rows_from_bullets(bullets),
                caption="Structured data summary",
            ),
            ChartBlock(
                block_id=f"{slide_id}_chart",
                title="Evidence weight by signal",
                categories=tuple(_short_label(bullet, fallback=f"S{i + 1}") for i, bullet in enumerate(bullets)),
                values=tuple(float(_weight_for_bullet(bullet)) for bullet in bullets),
                unit="pts",
            ),
        )
    if slide_type is SlideType.CONTENT:
        return (BulletBlock(block_id=f"{slide_id}_bullets", bullets=bullets, heading="Key points"),)
    return (BulletBlock(block_id=f"{slide_id}_bullets", bullets=bullets, heading=title),)


def _split_items_for_comparison(bullets: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    midpoint = max(1, (len(bullets) + 1) // 2)
    left_items = bullets[:midpoint] or ("Current baseline",)
    right_items = bullets[midpoint:] or ("Recommended next step",)
    return left_items, right_items


def _timeline_items_from_bullets(bullets: tuple[str, ...]) -> tuple[TimelineItem, ...]:
    source_items = bullets or ("Start", "Execute", "Review")
    return tuple(
        TimelineItem(label=f"Step {index}", detail=bullet)
        for index, bullet in enumerate(source_items[:4], start=1)
    )


def _business_metrics_from_bullets(bullets: tuple[str, ...]) -> tuple[BusinessMetric, ...]:
    total_words = sum(len(bullet.split()) for bullet in bullets)
    return (
        BusinessMetric(label="Signals", value=str(len(bullets)), note="bounded slide inputs"),
        BusinessMetric(label="Evidence", value=str(total_words), note="source words used"),
        BusinessMetric(label="Priority", value=f"{max((_weight_for_bullet(bullet) for bullet in bullets), default=0)} pts", note="derived from bullet length"),
    )


def _table_rows_from_bullets(bullets: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        (f"S{index}", bullet, str(_weight_for_bullet(bullet)))
        for index, bullet in enumerate(bullets or ("No supporting detail provided",), start=1)
    )


def _weight_for_bullet(bullet: str) -> int:
    # Deterministic, honest local formatting signal based only on supplied text.
    return min(100, max(10, len(bullet.split()) * 10))


def _short_label(text: str, *, fallback: str) -> str:
    words = [word.strip(" ,;:-") for word in text.split() if word.strip(" ,;:-")]
    label = " ".join(words[:3]).strip()
    return label[:24] if label else fallback
