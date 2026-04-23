from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
            stage = StoryArcStage.ANALYSIS if slide_type in {SlideType.CONTENT, SlideType.DATA} else StoryArcStage.RECOMMENDATION

        planned_slides.append(
            PlannedSlide(
                slide_id=f"slide_{slide_number:03d}",
                slide_type=slide_type,
                story_arc_stage=stage,
                title=_plan_title_for_type(slide_type=slide_type, seed=segment),
                bullets=tuple(_bounded_bullets(segment)),
                speaker_notes=_speaker_notes_for_type(slide_type),
                layout_hint=_layout_hint_for_type(slide_type),
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
    if slide_type is SlideType.COMPARISON:
        return "two_column_comparison"
    if slide_type is SlideType.TIMELINE:
        return "timeline"
    if slide_type is SlideType.DATA:
        return "data_summary"
    if slide_type is SlideType.TITLE:
        return "title_slide"
    if slide_type in {SlideType.SECTION, SlideType.APPENDIX}:
        return "section_slide"
    if slide_type is SlideType.CONCLUSION:
        return "conclusion"
    return "title_and_bullets"
