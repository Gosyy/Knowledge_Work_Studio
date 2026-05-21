from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.integrations.llm import GigaChatProvider, LLMCompletionRequest, build_llm_provider
from backend.app.integrations.llm.gigachat_runtime import (
    GigaChatRuntimeSelectionError,
    build_gigachat_runtime_hardening_report,
    run_gigachat_completion_diagnostic,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_gigachat_runtime_hardening_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def direct_settings(**overrides: object) -> Settings:
    base = dict(
        app_env="production",
        deployment_mode="offline_intranet",
        llm_provider="gigachat",
        llm_transport_mode="direct_gigachat",
        gigachat_api_base_url="http://10.10.10.30:8080/api/v1",
        gigachat_auth_url="http://gigachat.internal/oauth",
        gigachat_client_id="client-id",
        gigachat_client_secret="client-secret",
        gigachat_timeout_seconds=3.0,
    )
    base.update(overrides)
    return Settings(**base)


def test_rf4_checker_reports_ready_gigachat_runtime_hardening() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "gigachat-runtime-hardening"
    assert payload["checkpoint"] == "RF4"
    assert payload["status"] == "ready"
    assert payload["direct_gigachat_default"] is True
    assert payload["server_3_gigachat_default_runtime"] is True
    assert payload["server_2_litellm_gateway_optional"] is True
    assert payload["dependency_versions_changed_by_rf4"] is False
    assert payload["dockerfiles_changed_by_rf4"] is False
    assert payload["api_endpoint_added_by_rf4"] is False
    assert payload["db_schema_migration_added_by_rf4"] is False
    assert payload["cloud_llm_added_by_rf4"] is False
    assert payload["silent_fallback_allowed_by_rf4"] is False
    assert payload["k_phase_started_by_rf4"] is False


def test_rf4_validates_direct_gigachat_offline_runtime_settings() -> None:
    report = build_gigachat_runtime_hardening_report(direct_settings())

    assert report.status == "ready"
    assert report.direct_gigachat_default is True
    assert report.direct_gigachat_config_ready is True
    assert report.no_silent_fallback is True
    assert report.no_litellm_override is True
    assert report.no_ollama_override is True
    assert report.no_public_internet_runtime is True
    assert report.credentials_configured is True
    assert report.safe_metadata["raw_secret_values_stored"] is False


def test_rf4_rejects_public_endpoint_and_production_fake_provider() -> None:
    public_report = build_gigachat_runtime_hardening_report(
        direct_settings(
            gigachat_api_base_url="https://api.public.example/v1",
            gigachat_auth_url="https://auth.public.example/oauth",
        )
    )
    assert public_report.status == "not_ready"
    assert public_report.no_public_internet_runtime is False
    assert any("private/internal" in error for error in public_report.errors)

    with pytest.raises(GigaChatRuntimeSelectionError, match="requires LLM_PROVIDER=gigachat"):
        build_llm_provider(Settings(app_env="production", deployment_mode="offline_intranet", llm_provider="fake"))


def test_rf4_default_factory_builds_direct_gigachat_without_litellm_override() -> None:
    provider = build_llm_provider(direct_settings())

    assert isinstance(provider, GigaChatProvider)
    assert provider.provider_name == "gigachat"
    assert provider.api_base_url == "http://10.10.10.30:8080/api/v1"


def test_rf4_mocked_gigachat_diagnostics_success_and_timeout_are_safe() -> None:
    def success_handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "http://gigachat.internal/oauth":
            return httpx.Response(200, json={"access_token": "token-redacted", "expires_in": 1800})
        return httpx.Response(200, json={"model": "GigaChat-Pro", "choices": [{"message": {"content": "ok"}}]})

    success_provider = GigaChatProvider(
        api_base_url="http://10.10.10.30:8080/api/v1",
        auth_url="http://gigachat.internal/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        http_client=httpx.Client(transport=httpx.MockTransport(success_handler)),
    )
    success = run_gigachat_completion_diagnostic(success_provider)
    assert success.status == "ready"
    assert success.response_text_present is True
    assert success.raw_exception_stored is False

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated timeout", request=request)

    timeout_provider = GigaChatProvider(
        api_base_url="http://10.10.10.30:8080/api/v1",
        auth_url="http://gigachat.internal/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        http_client=httpx.Client(transport=httpx.MockTransport(timeout_handler)),
    )
    timeout = run_gigachat_completion_diagnostic(timeout_provider)
    assert timeout.status == "failed"
    assert timeout.error_code == "gigachat_auth_timeout"
    assert timeout.raw_exception_stored is False
    encoded = json.dumps(timeout.as_dict(), sort_keys=True)
    assert "client-secret" not in encoded
    assert "Authorization" not in encoded
    assert "Bearer " not in encoded


def test_rf4_provider_complete_reports_timeout_with_operator_safe_error() -> None:
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated timeout", request=request)

    provider = GigaChatProvider(
        api_base_url="http://10.10.10.30:8080/api/v1",
        auth_url="http://gigachat.internal/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        http_client=httpx.Client(transport=httpx.MockTransport(timeout_handler)),
    )

    with pytest.raises(Exception, match="timed out"):
        provider.complete(LLMCompletionRequest(prompt="hello"))
