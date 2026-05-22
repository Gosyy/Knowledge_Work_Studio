from __future__ import annotations

import pytest

from backend.app.core.config import Settings
from backend.app.deployment import build_deployment_readiness
from backend.app.integrations.llm import GigaChatProvider, build_llm_provider
from backend.app.integrations.llm.gigachat_runtime import (
    GigaChatRuntimeSelectionError,
    build_gigachat_runtime_hardening_report,
)


def public_gigachat_settings(**overrides: object) -> Settings:
    base = dict(
        app_env="production",
        deployment_mode="offline_intranet",
        gigachat_runtime_mode="public_internet_test",
        llm_provider="gigachat",
        llm_transport_mode="direct_gigachat",
        gigachat_api_base_url="https://gigachat.devices.sberbank.ru/api/v1",
        gigachat_auth_url="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        gigachat_client_id="client-id",
        gigachat_client_secret="client-secret",
        gigachat_timeout_seconds=3.0,
        metadata_backend="postgres",
        sqlite_runtime_allowed=False,
        database_url="postgresql://kwstudio:secret@postgres:5432/kwstudio",
        storage_backend="local",
        storage_root="/app/storage",
        uploads_dir="/app/storage/uploads",
        artifacts_dir="/app/storage/artifacts",
        temp_dir="/app/storage/temp",
        secret_key="test-secret-key-with-enough-length",
    )
    base.update(overrides)
    return Settings(**base)


def test_public_gigachat_test_mode_allows_public_direct_endpoints_explicitly() -> None:
    settings = public_gigachat_settings()

    report = build_gigachat_runtime_hardening_report(settings)
    provider = build_llm_provider(settings)

    assert report.status == "ready"
    assert report.no_public_internet_runtime is False
    assert report.safe_metadata["public_internet_test_mode"] is True
    assert report.safe_metadata["public_internet_test_is_offline_proof"] is False
    assert any("operator internet tests only" in warning for warning in report.warnings)
    assert isinstance(provider, GigaChatProvider)


def test_public_gigachat_endpoints_still_fail_without_explicit_test_mode() -> None:
    settings = public_gigachat_settings(gigachat_runtime_mode="offline_intranet")

    report = build_gigachat_runtime_hardening_report(settings)

    assert report.status == "not_ready"
    assert any("private/internal" in error for error in report.errors)
    with pytest.raises(GigaChatRuntimeSelectionError, match="private/internal"):
        build_llm_provider(settings)


def test_public_gigachat_test_mode_is_not_offline_deployment_proof() -> None:
    readiness = build_deployment_readiness(public_gigachat_settings())

    assert readiness.status == "ready"
    assert readiness.checks["public_gigachat_test_mode_explicit"] is True
    assert any("must not be treated as offline/intranet deployment proof" in warning for warning in readiness.warnings)


def test_public_gigachat_test_mode_rejects_unsupported_transport() -> None:
    settings = public_gigachat_settings(
        llm_transport_mode="litellm_gateway",
        litellm_gateway_url="http://10.0.0.2:4000",
    )

    report = build_gigachat_runtime_hardening_report(settings)

    assert report.status == "not_ready"
    assert "public_internet_test requires LLM_PROVIDER=gigachat and LLM_TRANSPORT_MODE=direct_gigachat" in report.errors
