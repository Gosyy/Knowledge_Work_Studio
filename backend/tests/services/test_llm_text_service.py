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
