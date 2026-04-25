from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Protocol

from backend.app.services.llm_text_service import LLMTextService
from backend.app.services.slides_service.outline import PlannedSlide


class SlideRevisionStrategy(Protocol):
    def revise_slide(
        self,
        slide: PlannedSlide,
        *,
        instruction: str,
        task_id: str | None = None,
    ) -> PlannedSlide: ...


@dataclass(frozen=True)
class DeterministicRevisionStrategy:
    def revise_slide(
        self,
        slide: PlannedSlide,
        *,
        instruction: str,
        task_id: str | None = None,
    ) -> PlannedSlide:
        clean_instruction = _clean_instruction(instruction)
        revised_title = _revision_title(slide.title, clean_instruction)
        revised_bullets = _revision_bullets(clean_instruction)
        speaker_notes = _append_revision_note(slide.speaker_notes, clean_instruction)
        return replace(
            slide,
            title=revised_title,
            bullets=revised_bullets,
            speaker_notes=speaker_notes,
        )


@dataclass(frozen=True)
class LLMRevisionStrategy:
    text_service: LLMTextService

    def revise_slide(
        self,
        slide: PlannedSlide,
        *,
        instruction: str,
        task_id: str | None = None,
    ) -> PlannedSlide:
        clean_instruction = _clean_instruction(instruction)
        response_text = self.text_service.complete_prompt(
            _revision_prompt(slide=slide, instruction=clean_instruction),
            system_prompt=(
                "You revise one presentation slide. "
                "Return strict JSON only with keys: title, bullets, speaker_notes. "
                "Do not include markdown fences or commentary."
            ),
            workflow="slide_revision",
            task_id=task_id,
        )
        payload = _parse_llm_revision_payload(response_text)
        return replace(
            slide,
            title=payload.title,
            bullets=payload.bullets,
            speaker_notes=payload.speaker_notes,
        )


@dataclass(frozen=True)
class LLMRevisionPayload:
    title: str
    bullets: tuple[str, ...]
    speaker_notes: str | None


def _revision_prompt(*, slide: PlannedSlide, instruction: str) -> str:
    return json.dumps(
        {
            "instruction": instruction,
            "slide": {
                "slide_id": slide.slide_id,
                "slide_type": slide.slide_type.value,
                "story_arc_stage": slide.story_arc_stage.value,
                "title": slide.title,
                "bullets": list(slide.bullets),
                "speaker_notes": slide.speaker_notes,
                "layout_hint": slide.layout_hint,
            },
            "required_output": {
                "title": "short revised slide title",
                "bullets": ["2-4 concise revised bullets"],
                "speaker_notes": "concise speaker note or null",
            },
        },
        ensure_ascii=False,
    )


def _parse_llm_revision_payload(response_text: str) -> LLMRevisionPayload:
    raw = _strip_optional_json_fence(response_text)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM slide revision returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("LLM slide revision must return a JSON object.")

    title = payload.get("title")
    bullets = payload.get("bullets")
    speaker_notes = payload.get("speaker_notes")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("LLM slide revision JSON must include a non-empty string title.")
    if not isinstance(bullets, list) or not bullets:
        raise ValueError("LLM slide revision JSON must include a non-empty bullets list.")
    if not all(isinstance(item, str) and item.strip() for item in bullets):
        raise ValueError("LLM slide revision bullets must be non-empty strings.")
    if speaker_notes is not None and not isinstance(speaker_notes, str):
        raise ValueError("LLM slide revision speaker_notes must be string or null.")

    return LLMRevisionPayload(
        title=title.strip(),
        bullets=tuple(item.strip() for item in bullets),
        speaker_notes=speaker_notes.strip() if isinstance(speaker_notes, str) and speaker_notes.strip() else None,
    )


def _strip_optional_json_fence(value: str) -> str:
    text = value.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _clean_instruction(instruction: str) -> str:
    clean_instruction = " ".join(instruction.split()).strip()
    if not clean_instruction:
        raise ValueError("Revision instruction must not be empty.")
    return clean_instruction


def _revision_title(previous_title: str, instruction: str) -> str:
    words = instruction.split()
    suffix = " ".join(words[:6]).strip()
    if not suffix:
        return previous_title
    return f"{previous_title[:36]} — revised: {suffix}"[:72]


def _revision_bullets(instruction: str) -> tuple[str, ...]:
    words = instruction.split()
    if not words:
        return ("Revision requested without detail",)
    chunks: list[str] = []
    for start in range(0, min(len(words), 36), 12):
        chunk = " ".join(words[start : start + 12]).strip()
        if chunk:
            chunks.append(chunk)
        if len(chunks) >= 3:
            break
    return tuple(chunks or ("Revision requested without detail",))


def _append_revision_note(existing_notes: str | None, instruction: str) -> str:
    revision_note = f"Revision instruction: {instruction}"
    if existing_notes:
        return f"{existing_notes}\n{revision_note}"
    return revision_note
