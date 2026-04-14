from datetime import datetime, timezone
from pathlib import Path

from backend.app.domain import LLMRun
from backend.app.repositories import SqliteLLMRunRepository


def test_i2_sqlite_llm_run_repository_persists_runs(tmp_path: Path) -> None:
    repository = SqliteLLMRunRepository(str(tmp_path / "llm_runs.sqlite3"))
    llm_run = LLMRun(
        id="llmrun_1",
        task_id="task_1",
        workflow="summarization",
        provider="gigachat",
        model="GigaChat-Pro",
        prompt="Summarize this",
        system_prompt="Be concise",
        response_text="summary",
        status="succeeded",
        error_message=None,
        raw_json={"id": "response-1"},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    repository.create(llm_run)

    assert repository.get("llmrun_1") == llm_run
    assert repository.list_by_task("task_1") == [llm_run]
    assert repository.list_by_workflow("summarization") == [llm_run]
