from __future__ import annotations

import base64
from dataclasses import dataclass, field
import time
from typing import Any
from uuid import uuid4

import httpx

from backend.app.integrations.llm.models import LLMCompletionRequest, LLMCompletionResult


@dataclass(frozen=True)
class FakeLLMProvider:
    response_text: str = "NOOP_LLM_RESPONSE"
    model_name: str = "fake-llm-v1"
    provider_name: str = "fake"

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        _ = request
        return LLMCompletionResult(
            text=self.response_text,
            provider=self.provider_name,
            model=self.model_name,
            raw={"mode": "fake"},
        )


class GigaChatProviderError(RuntimeError):
    """Raised when the GigaChat provider cannot complete a normalized request."""


@dataclass
class GigaChatProvider:
    api_base_url: str
    auth_url: str
    scope: str
    model_name: str
    client_id: str
    client_secret: str
    timeout_seconds: float = 30.0
    verify_ssl: bool = True
    provider_name: str = "gigachat"
    http_client: httpx.Client | None = field(default=None, repr=False)
    _access_token: str | None = field(default=None, init=False, repr=False)
    _token_expires_at: float = field(default=0.0, init=False, repr=False)

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        self._validate_config()
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(request),
            "temperature": request.temperature,
        }

        response = self._post_chat_completion(payload)
        if response.status_code == 401:
            self._clear_token()
            response = self._post_chat_completion(payload)

        try:
            response.raise_for_status()
            response_payload = response.json()
            text = self._extract_text(response_payload)
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise GigaChatProviderError("GigaChat completion request failed") from exc

        return LLMCompletionResult(
            text=text,
            provider=self.provider_name,
            model=str(response_payload.get("model") or self.model_name),
            raw=response_payload,
        )

    def _post_chat_completion(self, payload: dict[str, Any]) -> httpx.Response:
        token = self._get_access_token()
        return self._client.post(
            self._chat_completions_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    def _get_access_token(self) -> str:
        now = time.time()
        if self._access_token and self._token_expires_at - 30 > now:
            return self._access_token

        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        response = self._client.post(
            self.auth_url,
            headers={
                "Authorization": f"Basic {credentials}",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "RqUID": str(uuid4()),
            },
            data={"scope": self.scope},
        )
        try:
            response.raise_for_status()
            payload = response.json()
            token = str(payload["access_token"])
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise GigaChatProviderError("GigaChat OAuth token request failed") from exc

        self._access_token = token
        self._token_expires_at = self._parse_expires_at(payload)
        return token

    @property
    def _client(self) -> httpx.Client:
        if self.http_client is None:
            self.http_client = httpx.Client(timeout=self.timeout_seconds, verify=self.verify_ssl)
        return self.http_client

    @property
    def _chat_completions_url(self) -> str:
        return f"{self.api_base_url.rstrip('/')}/chat/completions"

    def _validate_config(self) -> None:
        missing = [
            name
            for name, value in {
                "gigachat_client_id": self.client_id,
                "gigachat_client_secret": self.client_secret,
                "gigachat_api_base_url": self.api_base_url,
                "gigachat_auth_url": self.auth_url,
                "gigachat_scope": self.scope,
                "gigachat_model": self.model_name,
            }.items()
            if not str(value or "").strip()
        ]
        if missing:
            raise ValueError(f"Missing GigaChat provider configuration: {', '.join(missing)}")

    @staticmethod
    def _build_messages(request: LLMCompletionRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        return str(payload["choices"][0]["message"]["content"])

    @staticmethod
    def _parse_expires_at(payload: dict[str, Any]) -> float:
        raw_expires_at = payload.get("expires_at")
        if isinstance(raw_expires_at, int | float):
            expires_at = float(raw_expires_at)
            if expires_at > 10_000_000_000:
                expires_at = expires_at / 1000
            return expires_at
        expires_in = payload.get("expires_in")
        if isinstance(expires_in, int | float):
            return time.time() + float(expires_in)
        return time.time() + 30 * 60

    def _clear_token(self) -> None:
        self._access_token = None
        self._token_expires_at = 0.0
