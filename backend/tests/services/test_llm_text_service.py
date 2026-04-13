from backend.app.integrations.llm import FakeLLMProvider
from backend.app.services.llm_text_service import LLMTextService


def test_llm_text_service_depends_on_provider_interface() -> None:
    service = LLMTextService(provider=FakeLLMProvider(response_text="from-provider"))
    assert service.complete_prompt("Say hi") == "from-provider"
