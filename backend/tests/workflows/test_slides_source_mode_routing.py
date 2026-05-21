from __future__ import annotations

from backend.app.services.slides_service.service import SlidesService


REAL_USER_PROMPT = (
    "Сгенерируй презентацию на 6 слайдов на тему: как компания может внедрить "
    "внутреннюю систему Knowledge Work Studio для работы с документами, таблицами, "
    "PDF, презентациями и проверяемыми артефактами. Стиль: деловой, понятно для "
    "руководителя, с краткими тезисами."
)


def test_prompt_only_short_outline_stays_on_legacy_source_aware_path() -> None:
    result = SlidesService().generate_deck(
        "Roadmap intro. Risks. Launch plan.",
        source_mode="prompt_only",
    )

    assert result.outline[0].title.startswith("Slide 1:")
    assert result.outline[0].bullets == ("Roadmap intro",)
    assert result.planning_metadata is not None
    assert result.planning_metadata["planner_contract"] == "legacy_source_aware"


def test_uploaded_source_mode_preserves_source_fragments() -> None:
    result = SlidesService().generate_deck(
        "Uploaded opportunity. Uploaded plan.",
        source_mode="uploaded_source",
        source_refs=(
            {
                "kind": "uploaded_file",
                "source_id": "upl_source",
                "role": "primary_source",
                "source_file_id": "upl_source",
            },
        ),
    )

    assert result.outline[0].bullets == ("Uploaded opportunity",)
    assert result.source_grounding_metadata is not None
    assert result.source_grounding_metadata["citation_count"] == result.slide_count
    assert result.planning_metadata is not None
    assert result.planning_metadata["planner_contract"] == "legacy_source_aware"


def test_real_user_generation_prompt_uses_kr6c_user_prompt_path() -> None:
    result = SlidesService().generate_deck(REAL_USER_PROMPT, source_mode="prompt_only")

    assert result.slide_count == 6
    assert result.planning_metadata is not None
    assert result.planning_metadata["planner_contract"] == "real_user_prompt"
    assert result.planning_metadata["requested_slide_count"] == 6
    assert not result.outline[0].title.startswith("Slide 1:")
