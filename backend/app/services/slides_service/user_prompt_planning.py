from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from backend.app.services.slides_service.outline import (
    PlannedSlide,
    PresentationPlan,
    SlideOutlineItem,
    SlideType,
    StoryArcStage,
    _structured_blocks_for_slide,
)

_MIN_USER_SLIDES = 3
_MAX_USER_SLIDES = 12
_DEFAULT_USER_SLIDES = 6
_MAX_TITLE_CHARS = 72
_MAX_BULLET_CHARS = 115
_FORBIDDEN_PUBLIC_FRAGMENTS = (
    "Additional insight",
    "Local deterministic slide image generation",
    "Сгенерируй презентацию",
    "Generate a presentation",
    "Generate presentation",
)


@dataclass(frozen=True)
class UserPromptPlanningResult:
    plan: PresentationPlan
    metadata: dict[str, object]


@dataclass(frozen=True)
class _PromptIntent:
    topic: str
    style: str
    requested_slide_count: int


def build_user_prompt_presentation_plan(
    source_text: str,
    *,
    min_slides: int = 5,
    max_slides: int = 10,
    llm_text_service: object | None = None,
    task_id: str | None = None,
) -> UserPromptPlanningResult:
    """Build a user-facing slides plan without leaking prompt text or placeholders.

    The LLM path is opportunistic and validated. If it is unavailable or returns an
    invalid plan, the deterministic fallback still produces a bounded business
    deck rather than a prompt echo or placeholder slides.
    """

    intent = _extract_prompt_intent(source_text, min_slides=min_slides, max_slides=max_slides)
    llm_error_code: str | None = None

    if llm_text_service is not None:
        try:
            llm_plan = _build_plan_with_llm(
                llm_text_service=llm_text_service,
                source_text=source_text,
                intent=intent,
                task_id=task_id,
            )
            if llm_plan is not None:
                return UserPromptPlanningResult(
                    plan=llm_plan,
                    metadata={
                        "planning_mode": "llm_validated",
                        "llm_planning_used": True,
                        "requested_slide_count": intent.requested_slide_count,
                        "actual_slide_count": len(llm_plan.slides),
                        "prompt_echo_blocked": True,
                        "placeholder_leakage_blocked": True,
                    },
                )
            llm_error_code = "llm_plan_invalid"
        except Exception:
            llm_error_code = "llm_plan_failed"

    fallback_plan = _build_deterministic_user_plan(intent)
    return UserPromptPlanningResult(
        plan=fallback_plan,
        metadata={
            "planning_mode": "deterministic_user_prompt_fallback",
            "llm_planning_used": False,
            "llm_planning_error_code": llm_error_code,
            "requested_slide_count": intent.requested_slide_count,
            "actual_slide_count": len(fallback_plan.slides),
            "prompt_echo_blocked": True,
            "placeholder_leakage_blocked": True,
        },
    )


def _build_plan_with_llm(
    *,
    llm_text_service: object,
    source_text: str,
    intent: _PromptIntent,
    task_id: str | None,
) -> PresentationPlan | None:
    complete_prompt = getattr(llm_text_service, "complete_prompt", None)
    if complete_prompt is None:
        return None

    response = complete_prompt(
        _llm_user_prompt(source_text=source_text, intent=intent),
        system_prompt=_llm_system_prompt(),
        workflow="slides_user_prompt_plan",
        task_id=task_id,
    )
    payload = _extract_json_object(str(response))
    if not payload:
        return None
    slides_payload = payload.get("slides")
    if not isinstance(slides_payload, list):
        return None

    slides: list[PlannedSlide] = []
    for index, raw_slide in enumerate(slides_payload[: intent.requested_slide_count], start=1):
        if not isinstance(raw_slide, dict):
            return None
        title = _clean_public_text(str(raw_slide.get("title") or ""), fallback=f"Слайд {index}")
        bullets_raw = raw_slide.get("bullets")
        if not isinstance(bullets_raw, list):
            return None
        bullets = tuple(
            _clean_public_text(str(item), fallback="Ключевой тезис")
            for item in bullets_raw[:5]
            if str(item).strip()
        )
        if len(bullets) < 2:
            return None
        slide_type = _slide_type_for_position(index, intent.requested_slide_count)
        slides.append(_planned_slide(index=index, slide_type=slide_type, title=title, bullets=bullets))

    if len(slides) != intent.requested_slide_count:
        return None
    if _plan_has_forbidden_fragments(slides):
        return None

    deck_title = _clean_public_text(
        str(payload.get("deck_title") or slides[0].title),
        fallback=_deck_title_for_topic(intent.topic),
    )
    return PresentationPlan(
        deck_title=deck_title,
        deck_goal="Создать деловую презентацию по пользовательскому запросу без утечки текста промпта и служебных маркеров.",
        audience="business_decision_makers",
        tone=intent.style or "деловой, краткий, понятный",
        target_slide_count=intent.requested_slide_count,
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=tuple(slides),
    )


def _build_deterministic_user_plan(intent: _PromptIntent) -> PresentationPlan:
    title = _deck_title_for_topic(intent.topic)
    slide_specs = _business_slide_specs(intent)
    slides = tuple(
        _planned_slide(index=index, slide_type=_slide_type_for_position(index, intent.requested_slide_count), title=spec_title, bullets=tuple(spec_bullets))
        for index, (spec_title, spec_bullets) in enumerate(slide_specs, start=1)
    )
    return PresentationPlan(
        deck_title=title,
        deck_goal="Дать руководителю понятный план внедрения с этапами, контролями и ожидаемым результатом.",
        audience="business_decision_makers",
        tone=intent.style or "деловой, краткий, понятный",
        target_slide_count=intent.requested_slide_count,
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


def _business_slide_specs(intent: _PromptIntent) -> list[tuple[str, list[str]]]:
    topic = _short_topic(intent.topic)
    base: list[tuple[str, list[str]]] = [
        (
            f"Зачем внедрять {topic}",
            [
                "Сократить ручную подготовку документов и презентаций",
                "Сделать результаты проверяемыми через артефакты и provenance",
                "Сохранить контроль оператора над критичными решениями",
            ],
        ),
        (
            "Проблемы текущего процесса",
            [
                "Файлы, промпты и результаты часто живут разрозненно",
                "Сложно проверить источники, версии и качество результата",
                "Повторяемые knowledge-work задачи требуют единого workflow",
            ],
        ),
        (
            "Целевая модель работы",
            [
                "Пользователь задаёт намерение и прикладывает источники",
                "Система строит план, запускает контролируемые инструменты",
                "На выходе формируются артефакты, отчёты качества и история",
            ],
        ),
        (
            "Ключевые workflow-пиллары",
            [
                "DOCX, PDF, XLSX и презентации обрабатываются как first-class workflows",
                "Python-анализ помогает проверять данные и строить расчёты",
                "Browser evidence добавляет проверяемые внешние источники",
            ],
        ),
        (
            "План внедрения",
            [
                "Начать с пилота на ограниченном наборе бизнес-сценариев",
                "Настроить роли, хранение, GigaChat runtime и validation gates",
                "Расширять workflows только после измеримого качества артефактов",
            ],
        ),
        (
            "Ожидаемый эффект и следующий шаг",
            [
                "Руководитель получает скачиваемые файлы и прозрачный audit trail",
                "Команды быстрее готовят материалы без потери проверяемости",
                "Следующий шаг — выбрать пилотный процесс и критерии ACCEPT",
            ],
        ),
    ]
    if intent.requested_slide_count < len(base):
        return _compress_specs(base, intent.requested_slide_count)
    while len(base) < intent.requested_slide_count:
        base.insert(
            -1,
            (
                f"Контроль качества: этап {len(base)}",
                [
                    "Проверить полноту артефактов и отсутствие служебных заглушек",
                    "Зафиксировать источники, ограничения и действия оператора",
                    "Не переводить сценарий в production без full runner и smoke checks",
                ],
            ),
        )
    return base[: intent.requested_slide_count]


def _compress_specs(specs: list[tuple[str, list[str]]], count: int) -> list[tuple[str, list[str]]]:
    if count <= 3:
        return [specs[0], specs[2], specs[-1]][:count]
    keep = [specs[0], specs[1], specs[2], specs[-1]]
    while len(keep) < count:
        keep.insert(-1, specs[len(keep)])
    return keep[:count]


def _extract_prompt_intent(source_text: str, *, min_slides: int, max_slides: int) -> _PromptIntent:
    requested = _extract_requested_slide_count(source_text)
    lower_bound = min(_MIN_USER_SLIDES, min_slides)
    upper_bound = max(_MAX_USER_SLIDES, max_slides)
    if requested is None:
        inferred = _segment_count(source_text) or _DEFAULT_USER_SLIDES
        slide_count = max(min_slides, min(max_slides, inferred))
    else:
        slide_count = max(lower_bound, min(upper_bound, requested))
    topic = _extract_topic(source_text)
    style = _extract_style(source_text)
    return _PromptIntent(topic=topic, style=style, requested_slide_count=slide_count)


def _segment_count(source_text: str) -> int:
    normalized = source_text.replace("\n", ". ")
    return len([segment for segment in normalized.split(".") if segment.strip()])


def _extract_requested_slide_count(source_text: str) -> int | None:
    patterns = (
        r"(?:на|из|for)\s+(\d{1,2})\s+(?:слайд|слайда|слайдов|slide|slides)",
        r"(\d{1,2})\s+(?:слайд|слайда|слайдов|slide|slides)",
    )
    for pattern in patterns:
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _extract_topic(source_text: str) -> str:
    text = " ".join(source_text.replace("\n", " ").split())
    topic_match = re.search(r"(?:на тему|about|topic)[:\s]+(.+?)(?:\bСтиль\s*:|\bStyle\s*:|$)", text, flags=re.IGNORECASE)
    if topic_match:
        return _clean_public_text(topic_match.group(1), fallback="внедрение Knowledge Work Studio")
    cleaned = re.sub(
        r"^(?:сгенерируй|создай|подготовь|generate|create|prepare)\s+(?:презентацию|presentation|deck).*?(?:на тему|about|topic)[:\s]+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = re.split(r"\b(?:Стиль|Style)\s*:", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    return _clean_public_text(cleaned, fallback="внедрение Knowledge Work Studio")


def _extract_style(source_text: str) -> str:
    match = re.search(r"(?:Стиль|Style)\s*:\s*(.+)$", source_text.replace("\n", " "), flags=re.IGNORECASE)
    if not match:
        return "деловой, понятный для руководителя, с краткими тезисами"
    return _clean_public_text(match.group(1), fallback="деловой, понятный для руководителя, с краткими тезисами")


def _deck_title_for_topic(topic: str) -> str:
    topic = _short_topic(topic)
    return f"Внедрение {topic}" if not topic.lower().startswith("внедрение") else topic


def _short_topic(topic: str) -> str:
    cleaned = _clean_public_text(topic, fallback="Knowledge Work Studio")
    replacements = (
        "как компания может внедрить внутреннюю систему ",
        "как компания может внедрить ",
        "как внедрить ",
    )
    lowered = cleaned.lower()
    for prefix in replacements:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    return cleaned[:80].strip(" .:;-—") or "Knowledge Work Studio"


def _slide_type_for_position(index: int, count: int) -> SlideType:
    if index == 1:
        return SlideType.TITLE
    if index == count:
        return SlideType.CONCLUSION
    if index == 2:
        return SlideType.SECTION
    if index == 4:
        return SlideType.COMPARISON
    if index == 5 and count >= 6:
        return SlideType.TIMELINE
    if index == count - 1 and count >= 7:
        return SlideType.DATA
    return SlideType.CONTENT


def _planned_slide(*, index: int, slide_type: SlideType, title: str, bullets: tuple[str, ...]) -> PlannedSlide:
    if index == 1:
        stage = StoryArcStage.OPENING
    elif index == 2:
        stage = StoryArcStage.CONTEXT
    elif index == 4:
        stage = StoryArcStage.RECOMMENDATION
    elif slide_type is SlideType.CONCLUSION:
        stage = StoryArcStage.CLOSE
    else:
        stage = StoryArcStage.ANALYSIS
    cleaned_title = _clean_public_text(title, fallback=f"Слайд {index}")
    cleaned_bullets = tuple(_clean_public_text(bullet, fallback="Ключевой тезис") for bullet in bullets if bullet.strip())[:5]
    return PlannedSlide(
        slide_id=f"user_prompt_{index:03d}",
        slide_type=slide_type,
        story_arc_stage=stage,
        title=cleaned_title,
        bullets=cleaned_bullets,
        speaker_notes="Кратко объяснить тезисы и связать с решением руководителя.",
        layout_hint="title_and_bullets",
        blocks=_structured_blocks_for_slide(
            slide_id=f"user_prompt_{index:03d}",
            slide_type=slide_type,
            title=cleaned_title,
            bullets=cleaned_bullets,
        ),
    )


def _clean_public_text(value: str, *, fallback: str) -> str:
    text = " ".join(value.replace("\n", " ").split()).strip(" \t-–—•")
    for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS:
        text = text.replace(fragment, "").strip(" \t-–—•:.")
    text = re.sub(r"^[:;,.\s]+", "", text)
    if not text:
        return fallback
    if len(text) > _MAX_BULLET_CHARS:
        text = text[:_MAX_BULLET_CHARS].rsplit(" ", 1)[0].strip() or text[:_MAX_TITLE_CHARS]
    return text


def _plan_has_forbidden_fragments(slides: list[PlannedSlide]) -> bool:
    joined = "\n".join([slide.title for slide in slides] + [bullet for slide in slides for bullet in slide.bullets])
    return any(fragment in joined for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS)


def _llm_system_prompt() -> str:
    return (
        "Ты планировщик деловых презентаций KW Studio. Верни только JSON без markdown. "
        "Не копируй команду пользователя как заголовок. Не используй заглушки. "
        "JSON schema: {\"deck_title\": string, \"slides\": [{\"title\": string, \"bullets\": [string, string]}]}."
    )


def _llm_user_prompt(*, source_text: str, intent: _PromptIntent) -> str:
    return (
        f"Создай план презентации ровно на {intent.requested_slide_count} слайдов.\n"
        f"Тема: {intent.topic}\n"
        f"Стиль: {intent.style}\n"
        "Каждый слайд: короткий деловой заголовок и 2-5 содержательных тезисов.\n"
        "Запрещено включать в результат служебные слова prompt, Additional insight, deterministic, Local deterministic.\n\n"
        f"Исходный запрос пользователя:\n{source_text}"
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def user_plan_to_outline(plan: PresentationPlan) -> tuple[SlideOutlineItem, ...]:
    return tuple(SlideOutlineItem(title=slide.title, bullets=slide.bullets) for slide in plan.slides)
