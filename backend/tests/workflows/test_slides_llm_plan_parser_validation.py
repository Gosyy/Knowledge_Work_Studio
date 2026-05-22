from backend.app.services.slides_service.service import SlidesService

PROMPT = "Сгенерируй презентацию на 6 слайдов на тему внедрения KW Studio."


def _ok_plan() -> str:
    return '{"schema_version":"slides_plan.v1","deck_title":"T","slides":[{"slide_number":1,"title":"Цель внедрения","bullets":["Бизнес-ценность для компании","Снижение операционных рисков"]},{"slide_number":2,"title":"Текущий контур","bullets":["Разрозненные документы и таблицы","Нет единого процесса контроля"]},{"slide_number":3,"title":"Целевая модель","bullets":["Процессы идут через workflow-контракты","Артефакты сохраняют provenance"]},{"slide_number":4,"title":"Пилот","bullets":["Старт с приоритетных сценариев","Контроль качества на этапах"]},{"slide_number":5,"title":"Запуск","bullets":["Роли и процедуры утверждены","Метрики качества формализованы"]},{"slide_number":6,"title":"Эффект","bullets":["Быстрее цикл подготовки","Выше предсказуемость результата"]}]}'


class _LLM:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete_prompt(self, *_args, **_kwargs):
        return self.response


def _assert_error(response: str, code: str) -> None:
    result = SlidesService(llm_text_service=_LLM(response)).generate_deck(PROMPT)
    assert result.planning_metadata is not None
    assert result.planning_metadata["llm_final_error_code"] == code


def test_parser_accepts_plain_fenced_and_wrapped_json() -> None:
    for variant in [
        _ok_plan(),
        f"```json\n{_ok_plan()}\n```",
        f"prefix text\n{_ok_plan()}\nsuffix",
    ]:
        result = SlidesService(llm_text_service=_LLM(variant)).generate_deck(PROMPT)
        assert result.planning_metadata is not None
        assert result.planning_metadata["llm_planning_used"] is True


def test_validation_error_matrix() -> None:
    _assert_error('{', 'no_json_object')
    _assert_error('no object here', 'no_json_object')
    _assert_error('[1,2,3]', 'no_json_object')
    _assert_error('{"deck_title":"x","slides":[]}', 'missing_schema_version')
    _assert_error('{"schema_version":"slides_plan.v2","deck_title":"x","slides":[]}', 'unsupported_schema_version')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x"}', 'missing_slides')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":"bad"}', 'slides_not_array')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"A","bullets":["x","y"]}]}', 'wrong_slide_count')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"bullets":["x","y"]},{"slide_number":2,"title":"B","bullets":["x","y"]},{"slide_number":3,"title":"C","bullets":["x","y"]},{"slide_number":4,"title":"D","bullets":["x","y"]},{"slide_number":5,"title":"E","bullets":["x","y"]},{"slide_number":6,"title":"F","bullets":["x","y"]}]}', 'missing_title')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"Valid title","bullets":"bad"},{"slide_number":2,"title":"B2","bullets":["x","y"]},{"slide_number":3,"title":"C2","bullets":["x","y"]},{"slide_number":4,"title":"D2","bullets":["x","y"]},{"slide_number":5,"title":"E2","bullets":["x","y"]},{"slide_number":6,"title":"F2","bullets":["x","y"]}]}', 'bullets_not_array')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"title":"Title one","bullets":["v1","v2"]},{"slide_number":2,"title":"B2","bullets":["v1","v2"]},{"slide_number":3,"title":"C2","bullets":["v1","v2"]},{"slide_number":4,"title":"D2","bullets":["v1","v2"]},{"slide_number":5,"title":"E2","bullets":["v1","v2"]},{"slide_number":6,"title":"F2","bullets":["v1","v2"]}]}', 'missing_slide_number')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":2,"title":"Title one","bullets":["v1","v2"]},{"slide_number":2,"title":"B2","bullets":["v1","v2"]},{"slide_number":3,"title":"C2","bullets":["v1","v2"]},{"slide_number":4,"title":"D2","bullets":["v1","v2"]},{"slide_number":5,"title":"E2","bullets":["v1","v2"]},{"slide_number":6,"title":"F2","bullets":["v1","v2"]}]}', 'invalid_slide_number')

    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"Valid title","bullets":["one"]},{"slide_number":2,"title":"B2","bullets":["x","y"]},{"slide_number":3,"title":"C2","bullets":["x","y"]},{"slide_number":4,"title":"D2","bullets":["x","y"]},{"slide_number":5,"title":"E2","bullets":["x","y"]},{"slide_number":6,"title":"F2","bullets":["x","y"]}]}', 'too_few_bullets')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"Valid title","bullets":["1","2","3","4","5","6"]},{"slide_number":2,"title":"B2","bullets":["x","y"]},{"slide_number":3,"title":"C2","bullets":["x","y"]},{"slide_number":4,"title":"D2","bullets":["x","y"]},{"slide_number":5,"title":"E2","bullets":["x","y"]},{"slide_number":6,"title":"F2","bullets":["x","y"]}]}', 'too_many_bullets')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"Additional insight","bullets":["Бизнес ценность","Снижение рисков"]},{"slide_number":2,"title":"B2","bullets":["value","growth"]},{"slide_number":3,"title":"C2","bullets":["value","growth"]},{"slide_number":4,"title":"D2","bullets":["value","growth"]},{"slide_number":5,"title":"E2","bullets":["value","growth"]},{"slide_number":6,"title":"F2","bullets":["value","growth"]}]}', 'template_label_detected')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"Key points","bullets":["Бизнес ценность","Снижение рисков"]},{"slide_number":2,"title":"B2","bullets":["value","growth"]},{"slide_number":3,"title":"C2","bullets":["value","growth"]},{"slide_number":4,"title":"D2","bullets":["value","growth"]},{"slide_number":5,"title":"E2","bullets":["value","growth"]},{"slide_number":6,"title":"F2","bullets":["value","growth"]}]}', 'template_label_detected')
    _assert_error('{"schema_version":"slides_plan.v1","deck_title":"x","slides":[{"slide_number":1,"title":"A","bullets":["Бизнес ценность","Снижение рисков"]},{"slide_number":2,"title":"B2","bullets":["value","growth"]},{"slide_number":3,"title":"C2","bullets":["value","growth"]},{"slide_number":4,"title":"D2","bullets":["value","growth"]},{"slide_number":5,"title":"E2","bullets":["value","growth"]},{"slide_number":6,"title":"F2","bullets":["value","growth"]}]}', 'low_information_content')
