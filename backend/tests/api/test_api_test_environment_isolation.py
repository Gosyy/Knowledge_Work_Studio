from __future__ import annotations

import pytest

from backend.app.composition import resolve_metadata_backend
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm import FakeLLMProvider, build_llm_provider


def test_api_tests_run_under_test_environment_not_operator_production_env() -> None:
    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.metadata_backend == "sqlite"
    assert settings.sqlite_runtime_allowed is True
    assert settings.llm_provider == "fake"
    assert resolve_metadata_backend(settings) == "sqlite"


def test_production_sqlite_guardrail_remains_fail_closed() -> None:
    settings = Settings(
        app_env="production",
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
    )

    with pytest.raises(ValueError, match="SQLite metadata backend is only allowed"):
        resolve_metadata_backend(settings)


def test_api_test_environment_can_build_fake_llm_provider_without_offline_policy_error() -> None:
    provider = build_llm_provider(Settings(llm_provider="fake", fake_llm_response="api-test-response"))

    assert isinstance(provider, FakeLLMProvider)
    assert provider.response_text == "api-test-response"
