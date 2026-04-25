from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.services.slides_service import (
    DeckRevisionRequest,
    DeckRevisionService,
    DeterministicRevisionStrategy,
    LLMRevisionStrategy,
    PlannedSlide,
    SlideRevisionStrategy,
    SlideType,
    StoryArcStage,
    build_presentation_plan,
)


class _MemoryStorage:
    backend_name = "memory"

    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str:
        self.items[storage_key] = content
        return f"memory://{storage_key}"

    def read_bytes(self, *, storage_key: str) -> bytes:
        return self.items[storage_key]

    def exists(self, *, storage_key: str) -> bool:
        return storage_key in self.items

    def delete(self, *, storage_key: str) -> None:
        self.items.pop(storage_key, None)

    def get_size(self, *, storage_key: str) -> int | None:
        item = self.items.get(storage_key)
        return len(item) if item is not None else None

    def make_uri(self, *, storage_key: str) -> str:
        return f"memory://{storage_key}"


class _StoredFiles:
    def __init__(self) -> None:
        self.items: dict[str, StoredFile] = {}

    def create(self, stored_file: StoredFile) -> StoredFile:
        self.items[stored_file.id] = stored_file
        return stored_file

    def get(self, stored_file_id: str) -> StoredFile | None:
        return self.items.get(stored_file_id)

    def list_by_session(self, session_id: str) -> list[StoredFile]:
        return [item for item in self.items.values() if item.session_id == session_id]


class _Presentations:
    def __init__(self, presentation: Presentation | None = None) -> None:
        self.items: dict[str, Presentation] = {}
        if presentation is not None:
            self.items[presentation.id] = presentation

    def create(self, presentation: Presentation) -> Presentation:
        self.items[presentation.id] = presentation
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        return self.items.get(presentation_id)

    def list_by_session(self, session_id: str) -> list[Presentation]:
        return [item for item in self.items.values() if item.session_id == session_id]


class _PresentationVersions:
    def __init__(self, versions: tuple[PresentationVersion, ...] = ()) -> None:
        self.items: list[PresentationVersion] = list(versions)

    def create(self, presentation_version: PresentationVersion) -> PresentationVersion:
        self.items.append(presentation_version)
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[PresentationVersion]:
        return [item for item in self.items if item.presentation_id == presentation_id]


class RecordingRevisionStrategy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []

    def revise_slide(
        self,
        slide: PlannedSlide,
        *,
        instruction: str,
        task_id: str | None = None,
    ) -> PlannedSlide:
        self.calls.append((slide.slide_id, instruction, task_id))
        return replace(
            slide,
            title=f"Strategy revised {slide.slide_id}",
            bullets=(f"strategy bullet for {slide.slide_id}",),
            speaker_notes=f"strategy task={task_id}",
        )


class FakeLLMTextService:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def complete_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        workflow: str = "completion",
        task_id: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "workflow": workflow,
                "task_id": task_id,
            }
        )
        return self.response


class FailingLLMTextService:
    def complete_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        workflow: str = "completion",
        task_id: str | None = None,
    ) -> str:
        raise RuntimeError("provider unavailable")


def _service_with_strategy(strategy: SlideRevisionStrategy) -> DeckRevisionService:
    presentation = Presentation(
        id="pres_n4",
        session_id="ses_n4",
        current_file_id="sf_initial_n4",
        presentation_type="generated_deck",
        title="N4 deck",
    )
    versions = _PresentationVersions(
        (
            PresentationVersion(
                id="presver_initial_n4",
                presentation_id="pres_n4",
                file_id="sf_initial_n4",
                version_number=1,
                created_from_task_id="task_initial_n4",
                parent_version_id=None,
                change_summary="Initial deck",
            ),
        )
    )
    return DeckRevisionService(
        storage=_MemoryStorage(),
        stored_files=_StoredFiles(),
        presentations=_Presentations(presentation),
        presentation_versions=versions,
        revision_strategy=strategy,
    )


def _sample_slide() -> PlannedSlide:
    return PlannedSlide(
        slide_id="slide_001",
        slide_type=SlideType.CONTENT,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="Original title",
        bullets=("Original bullet",),
        speaker_notes="Original notes",
        layout_hint="content_with_visual",
    )


def test_n4_deterministic_revision_strategy_preserves_m15_behavior() -> None:
    slide = _sample_slide()
    strategy = DeterministicRevisionStrategy()

    revised = strategy.revise_slide(
        slide,
        instruction="Emphasize delivery risk and shorten the recommendation.",
        task_id="task_n4",
    )

    assert revised.title.startswith("Original title — revised:")
    assert revised.bullets == ("Emphasize delivery risk and shorten the recommendation.",)
    assert "Revision instruction: Emphasize delivery risk" in (revised.speaker_notes or "")
    assert revised.slide_id == slide.slide_id
    assert revised.slide_type is slide.slide_type


def test_n4_deck_revision_service_delegates_single_slide_to_strategy() -> None:
    strategy = RecordingRevisionStrategy()
    service = _service_with_strategy(strategy)
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )

    result = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_n4",
            plan=plan,
            target_slide_index=2,
            instruction="Use strategy for one slide.",
            task_id="task_n4",
        )
    )

    assert strategy.calls == [("slide_003", "Use strategy for one slide.", "task_n4")]
    assert result.revised_plan.slides[2].title == "Strategy revised slide_003"
    assert result.deltas[0].new_bullets == ("strategy bullet for slide_003",)


def test_n4_deck_revision_service_delegates_section_to_strategy() -> None:
    strategy = RecordingRevisionStrategy()
    service = _service_with_strategy(strategy)
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )

    result = service.regenerate_section(
        DeckRevisionRequest(
            presentation_id="pres_n4",
            plan=plan,
            target_stage=StoryArcStage.ANALYSIS,
            instruction="Use strategy for analysis section.",
            task_id="task_section_n4",
        )
    )

    assert strategy.calls == [
        ("slide_003", "Use strategy for analysis section.", "task_section_n4"),
        ("slide_006", "Use strategy for analysis section.", "task_section_n4"),
    ]
    assert set(result.revised_slide_ids) == {"slide_003", "slide_006"}


def test_n4_llm_revision_strategy_uses_text_service_response() -> None:
    text_service = FakeLLMTextService(
        '{"title": "LLM revised title", "bullets": ["LLM bullet one", "LLM bullet two"], "speaker_notes": "LLM notes"}'
    )
    strategy = LLMRevisionStrategy(text_service=text_service)  # type: ignore[arg-type]

    revised = strategy.revise_slide(
        _sample_slide(),
        instruction="Rewrite with stronger executive framing.",
        task_id="task_llm_n4",
    )

    assert revised.title == "LLM revised title"
    assert revised.bullets == ("LLM bullet one", "LLM bullet two")
    assert revised.speaker_notes == "LLM notes"
    assert text_service.calls[0]["workflow"] == "slide_revision"
    assert text_service.calls[0]["task_id"] == "task_llm_n4"


def test_n4_llm_revision_strategy_fails_honestly_on_provider_error() -> None:
    strategy = LLMRevisionStrategy(text_service=FailingLLMTextService())  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="provider unavailable"):
        strategy.revise_slide(
            _sample_slide(),
            instruction="This must not silently fall back.",
            task_id="task_fail_n4",
        )


def test_n4_llm_revision_strategy_rejects_invalid_json_without_fallback() -> None:
    strategy = LLMRevisionStrategy(text_service=FakeLLMTextService("not-json"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="invalid JSON"):
        strategy.revise_slide(
            _sample_slide(),
            instruction="This must fail instead of faking success.",
        )
