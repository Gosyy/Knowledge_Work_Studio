from backend.app.integrations.llm import (
    FakeLLMProvider,
    LLMCompletionRequest,
    LLMCompletionResult,
)
from backend.app.services.llm_text_service import LLMTextService


class RecordingProvider:
    provider_name = "recording"

    def __init__(self) -> None:
        self.calls: list[LLMCompletionRequest] = []

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        self.calls.append(request)
        return LLMCompletionResult(
            text="from-recording-provider",
            provider=self.provider_name,
            model="recording-v1",
            raw={"mode": "recording"},
        )


def test_llm_text_service_depends_on_provider_interface() -> None:
    service = LLMTextService(provider=FakeLLMProvider(response_text="from-provider"))
    assert service.complete_prompt("Say hi") == "from-provider"


def test_llm_text_service_accepts_protocol_compatible_provider() -> None:
    provider = RecordingProvider()
    service = LLMTextService(provider=provider)

    result = service.complete_prompt("Say hi", system_prompt="Be concise")

    assert result == "from-recording-provider"
    assert provider.calls == [
        LLMCompletionRequest(
            prompt="Say hi",
            system_prompt="Be concise",
        )
    ]


class SemanticRecordingProvider:
    provider_name = "gigachat"

    def __init__(self, responses: list[str] | None = None) -> None:
        self.calls: list[LLMCompletionRequest] = []
        self.responses = responses or ["provider-response"]

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        self.calls.append(request)
        return LLMCompletionResult(
            text=self.responses.pop(0),
            provider=self.provider_name,
            model="GigaChat-Pro",
            raw={"id": "resp-1"},
        )


class FailingProvider:
    provider_name = "gigachat"

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        _ = request
        raise RuntimeError("provider exploded")


class RecordingLLMRunRepository:
    def __init__(self) -> None:
        self.runs = []

    def create(self, llm_run):
        self.runs.append(llm_run)
        return llm_run

    def get(self, llm_run_id: str):
        return next((run for run in self.runs if run.id == llm_run_id), None)

    def list_by_task(self, task_id: str):
        return [run for run in self.runs if run.task_id == task_id]

    def list_by_workflow(self, workflow: str):
        return [run for run in self.runs if run.workflow == workflow]


def test_i2_semantic_workflows_use_provider_abstraction_and_persist_runs() -> None:
    provider = SemanticRecordingProvider(
        responses=[
            "pdf_summary",
            "summary",
            "rewritten",
            "outline",
        ]
    )
    llm_runs = RecordingLLMRunRepository()
    service = LLMTextService(provider=provider, llm_runs=llm_runs)

    assert service.classify_task("Summarize this PDF", task_id="task_1") == "pdf_summary"
    assert service.summarize_text("Long text", task_id="task_1") == "summary"
    assert service.rewrite_text("Draft", instruction="Make it formal", task_id="task_1") == "rewritten"
    assert service.generate_outline("Deck about Q1", task_id="task_1") == "outline"

    assert [run.workflow for run in llm_runs.runs] == [
        "classification",
        "summarization",
        "rewriting",
        "outline_generation",
    ]
    assert {run.provider for run in llm_runs.runs} == {"gigachat"}
    assert {run.model for run in llm_runs.runs} == {"GigaChat-Pro"}
    assert all(run.task_id == "task_1" for run in llm_runs.runs)
    assert all(run.status == "succeeded" for run in llm_runs.runs)
    assert len(provider.calls) == 4


def test_i2_failed_provider_call_is_persisted_before_reraising() -> None:
    llm_runs = RecordingLLMRunRepository()
    service = LLMTextService(provider=FailingProvider(), llm_runs=llm_runs)

    import pytest

    with pytest.raises(RuntimeError, match="provider exploded"):
        service.summarize_text("Long text", task_id="task_failed")

    assert len(llm_runs.runs) == 1
    run = llm_runs.runs[0]
    assert run.task_id == "task_failed"
    assert run.workflow == "summarization"
    assert run.provider == "gigachat"
    assert run.status == "failed"
    assert run.error_message == "provider exploded"
