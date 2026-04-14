import base64
import time

import httpx
import pytest

from backend.app.integrations.llm import GigaChatProvider, LLMCompletionRequest
from backend.app.integrations.llm.providers import GigaChatProviderError


def build_provider(handler) -> GigaChatProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return GigaChatProvider(
        api_base_url="https://gigachat.test/api/v1",
        auth_url="https://auth.test/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        http_client=client,
    )


def test_i1_gigachat_provider_gets_token_and_normalizes_completion() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url == "https://auth.test/oauth":
            assert request.headers["authorization"] == "Basic " + base64.b64encode(b"client-id:client-secret").decode()
            assert request.headers["rquid"]
            assert request.content == b"scope=GIGACHAT_API_PERS"
            return httpx.Response(
                200,
                json={"access_token": "token-1", "expires_at": int((time.time() + 1800) * 1000)},
            )

        assert request.url == "https://gigachat.test/api/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer token-1"
        payload = request.read().decode()
        assert '"model":"GigaChat-Pro"' in payload
        assert '"role":"system"' in payload
        assert '"role":"user"' in payload
        return httpx.Response(
            200,
            json={
                "model": "GigaChat-Pro",
                "choices": [{"message": {"content": "normalized answer"}}],
            },
        )

    provider = build_provider(handler)
    result = provider.complete(
        LLMCompletionRequest(
            system_prompt="Be concise",
            prompt="Hello",
            temperature=0.1,
        )
    )

    assert result.text == "normalized answer"
    assert result.provider == "gigachat"
    assert result.model == "GigaChat-Pro"
    assert len(requests) == 2


def test_i1_gigachat_provider_reuses_cached_token() -> None:
    auth_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal auth_calls
        if request.url == "https://auth.test/oauth":
            auth_calls += 1
            return httpx.Response(
                200,
                json={"access_token": "cached-token", "expires_at": int((time.time() + 1800) * 1000)},
            )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    provider = build_provider(handler)

    assert provider.complete(LLMCompletionRequest(prompt="one")).text == "ok"
    assert provider.complete(LLMCompletionRequest(prompt="two")).text == "ok"
    assert auth_calls == 1


def test_i1_gigachat_provider_refreshes_token_once_after_unauthorized_chat() -> None:
    token_calls = 0
    chat_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls, chat_calls
        if request.url == "https://auth.test/oauth":
            token_calls += 1
            return httpx.Response(
                200,
                json={"access_token": f"token-{token_calls}", "expires_at": int((time.time() + 1800) * 1000)},
            )

        chat_calls += 1
        if chat_calls == 1:
            assert request.headers["authorization"] == "Bearer token-1"
            return httpx.Response(401, json={"message": "expired"})
        assert request.headers["authorization"] == "Bearer token-2"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "after refresh"}}]},
        )

    provider = build_provider(handler)

    assert provider.complete(LLMCompletionRequest(prompt="hello")).text == "after refresh"
    assert token_calls == 2
    assert chat_calls == 2


def test_i1_gigachat_provider_wraps_bad_responses() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == "https://auth.test/oauth":
            return httpx.Response(200, json={"access_token": "token"})
        return httpx.Response(200, json={"choices": []})

    provider = build_provider(handler)

    with pytest.raises(GigaChatProviderError):
        provider.complete(LLMCompletionRequest(prompt="hello"))
