from __future__ import annotations

from io import BytesIO
import zipfile

from backend.app.services.slides_service.service import SlidesService


REAL_USER_PROMPT = (
    "Сгенерируй презентацию на 6 слайдов на тему: как компания может внедрить "
    "внутреннюю систему Knowledge Work Studio для работы с документами, таблицами, "
    "PDF, презентациями и проверяемыми артефактами. Стиль: деловой, понятно для "
    "руководителя, с краткими тезисами."
)

FORBIDDEN_TEXT = (
    "Additional insight",
    "Local deterministic slide image generation",
    "Сгенерируй презентацию",
)


def _pptx_xml(payload: bytes) -> str:
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx:
        return "\n".join(
            pptx.read(name).decode("utf-8", errors="replace")
            for name in pptx.namelist()
            if name.endswith(".xml")
        )


class _FakeSlidesPlanner:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def complete_prompt(self, prompt: str, *, system_prompt: str | None = None, workflow: str = "completion", task_id: str | None = None) -> str:
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt, "workflow": workflow, "task_id": task_id})
        return self.response


def test_real_user_prompt_generates_requested_count_without_placeholder_leakage() -> None:
    result = SlidesService().generate_deck(REAL_USER_PROMPT)

    assert result.slide_count == 6
    assert result.planning_metadata is not None
    assert result.planning_metadata["requested_slide_count"] == 6
    assert result.planning_metadata["placeholder_leakage_blocked"] is True

    outline_text = "\n".join(
        [item.title for item in result.outline] + [bullet for item in result.outline for bullet in item.bullets]
    )
    pptx_text = _pptx_xml(result.artifact_content)
    for forbidden in FORBIDDEN_TEXT:
        assert forbidden not in outline_text
        assert forbidden not in pptx_text

    assert "Knowledge Work Studio" in outline_text
    assert "проверяем" in outline_text.lower()


def test_valid_llm_plan_is_used_after_schema_validation() -> None:
    fake_llm = _FakeSlidesPlanner(
        """
        {
          "deck_title": "Внедрение KW Studio",
          "slides": [
            {"title": "Цель внедрения", "bullets": ["Сократить ручную работу", "Повысить проверяемость результатов"]},
            {"title": "Текущие проблемы", "bullets": ["Разрозненные файлы и версии", "Сложная проверка источников"]},
            {"title": "Целевая workflow-модель", "bullets": ["Промпт и источники превращаются в план", "Артефакты проходят validation gates"]},
            {"title": "Пилотные сценарии", "bullets": ["DOCX, PDF, XLSX и презентации", "Python-анализ и browser evidence"]},
            {"title": "План внедрения", "bullets": ["Начать с пилота", "Закрепить роли и критерии качества"]},
            {"title": "Ожидаемый эффект", "bullets": ["Быстрее готовить материалы", "Сохранять audit trail"]}
          ]
        }
        """
    )

    result = SlidesService(llm_text_service=fake_llm).generate_deck(REAL_USER_PROMPT, task_id="task_real_user")

    assert result.slide_count == 6
    assert result.planning_metadata is not None
    assert result.planning_metadata["planning_mode"] == "llm_validated"
    assert result.planning_metadata["llm_planning_used"] is True
    assert fake_llm.calls
    assert fake_llm.calls[0]["workflow"] == "slides_user_prompt_plan"


def test_invalid_llm_plan_falls_back_without_successful_placeholder_leakage() -> None:
    fake_llm = _FakeSlidesPlanner(
        '{"deck_title": "Bad", "slides": [{"title": "Additional insight 1", "bullets": ["Additional insight 1"]}]}'
    )

    result = SlidesService(llm_text_service=fake_llm).generate_deck(REAL_USER_PROMPT, task_id="task_bad_plan")

    assert result.slide_count == 6
    assert result.planning_metadata is not None
    assert result.planning_metadata["planning_mode"] == "deterministic_user_prompt_fallback"
    assert result.planning_metadata["llm_planning_used"] is False
    assert result.planning_metadata["llm_planning_error_code"] == "llm_plan_invalid"
    assert "Additional insight" not in _pptx_xml(result.artifact_content)
