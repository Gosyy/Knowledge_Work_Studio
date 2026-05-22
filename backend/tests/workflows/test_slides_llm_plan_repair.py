from backend.app.services.slides_service.service import SlidesService

PROMPT = "Сгенерируй презентацию на 6 слайдов на тему внедрения KW Studio."


class _RepairLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete_prompt(self, *_args, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return '{"schema_version":"slides_plan.v1","deck_title":"bad","slides":[{"title":"Only one","bullets":["x"]}]}'
        return '{"schema_version":"slides_plan.v1","deck_title":"OK","slides":[{"slide_number":1,"title":"A","bullets":["b1","b2"]},{"slide_number":2,"title":"B","bullets":["b1","b2"]},{"slide_number":3,"title":"C","bullets":["b1","b2"]},{"slide_number":4,"title":"D","bullets":["b1","b2"]},{"slide_number":5,"title":"E","bullets":["b1","b2"]},{"slide_number":6,"title":"F","bullets":["b1","b2"]}]}'


def test_llm_repair_attempt_succeeds() -> None:
    llm = _RepairLLM()
    result = SlidesService(llm_text_service=llm).generate_deck(PROMPT)
    assert result.planning_metadata is not None
    assert result.planning_metadata["planning_mode"] == "llm_repaired"
    assert result.planning_metadata["llm_attempt_count"] == 2
    assert result.slide_count == 6
