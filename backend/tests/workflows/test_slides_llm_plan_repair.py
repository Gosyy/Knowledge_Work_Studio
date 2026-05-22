from backend.app.services.slides_service.service import SlidesService

PROMPT = "Сгенерируй презентацию на 6 слайдов на тему внедрения KW Studio. Стиль: деловой."


class _RepairLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete_prompt(self, *_args, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return '{"schema_version":"slides_plan.v1","deck_title":"bad","slides":[{"slide_number":1,"title":"Only one","bullets":["x"]}]}'
        return '{"schema_version":"slides_plan.v1","deck_title":"Внедрение KW Studio","audience":"board","tone":"деловой","slides":[{"slide_number":1,"title":"Бизнес-цель внедрения","bullets":["Сократить ручную подготовку материалов","Улучшить управляемость знаний"]},{"slide_number":2,"title":"Проблемы текущего контура","bullets":["Данные и документы разрознены","Трудно проверять происхождение выводов"]},{"slide_number":3,"title":"Целевая операционная модель","bullets":["Единый workflow от источников к артефактам","Проверяемые quality gates на каждом шаге"]},{"slide_number":4,"title":"Пилотные сценарии","bullets":["DOCX/PDF/XLSX/Slides как обязательные столпы","Python и browser-evidence для проверки гипотез"]},{"slide_number":5,"title":"Дорожная карта запуска","bullets":["Пилот в одном бизнес-подразделении","Фиксация KPI качества и скорости"]},{"slide_number":6,"title":"Ожидаемый эффект","bullets":["Прозрачный audit trail для руководства","Снижение рисков ошибочных решений"]}]}'


def test_llm_repair_attempt_succeeds() -> None:
    llm = _RepairLLM()
    result = SlidesService(llm_text_service=llm).generate_deck(PROMPT)
    assert result.planning_metadata is not None
    assert result.planning_metadata["planning_mode"] == "llm_repaired"
    assert result.planning_metadata["llm_attempt_count"] == 2
    assert result.slide_count == 6
