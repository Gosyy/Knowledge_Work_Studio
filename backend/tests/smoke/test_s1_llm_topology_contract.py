from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.integrations.llm import build_llm_provider, build_llm_topology_contract
from backend.app.integrations.llm.providers import GigaChatProvider, LiteLLMCompatibleProvider

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON = os.environ.get("KW_TEST_PYTHON", sys.executable)


def run_topology_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/kw_llm_topology_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_env(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / ".env.deploy"
    env_file.write_text(content.strip() + "\n", encoding="utf-8")
    return env_file


def test_s1_default_direct_gigachat_provider_contract() -> None:
    settings = Settings(
        deployment_mode="offline_intranet",
        llm_provider="gigachat",
        llm_transport_mode="direct_gigachat",
        gigachat_api_base_url="http://10.0.0.3:8080/api",
        gigachat_auth_url="http://10.0.0.3:8080/auth",
        gigachat_client_id="client",
        gigachat_client_secret="secret",
    )

    provider = build_llm_provider(settings)
    contract = build_llm_topology_contract(settings)

    assert isinstance(provider, GigaChatProvider)
    assert contract.status == "ready"
    assert contract.default_provider == "gigachat"
    assert contract.server_roles["server_3"].startswith("Local GigaChat")


def test_s1_litellm_gateway_is_optional_transport_for_gigachat() -> None:
    settings = Settings(
        deployment_mode="offline_intranet",
        llm_provider="gigachat",
        llm_transport_mode="litellm_gateway",
        litellm_gateway_url="http://10.0.0.2:4000",
        litellm_gateway_model="gigachat-proxy",
        gigachat_model="GigaChat-Pro",
    )

    provider = build_llm_provider(settings)
    contract = build_llm_topology_contract(settings)

    assert isinstance(provider, LiteLLMCompatibleProvider)
    assert provider.model_name == "gigachat-proxy"
    assert contract.status == "ready"
    assert contract.optional_components["server_2_litellm_gateway"] is True
    assert "legacy_local_llm" not in contract.endpoints
    assert "legacy_local_llm_fallback_dev_only" not in contract.optional_components


def test_s1_offline_mode_rejects_non_gigachat_provider() -> None:
    settings = Settings(
        deployment_mode="offline_intranet",
        llm_provider="local_model",
        llm_transport_mode="direct_gigachat",
        gigachat_api_base_url="http://10.0.0.3:8080/api",
        gigachat_auth_url="http://10.0.0.3:8080/auth",
    )

    contract = build_llm_topology_contract(settings)

    assert contract.status == "not_ready"
    assert "offline_intranet requires LLM_PROVIDER=gigachat" in contract.errors


def test_s1_topology_cli_redacts_secrets_and_outputs_json(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path,
        """
        APP_ENV=production
        DEPLOYMENT_MODE=offline_intranet
        LLM_PROVIDER=gigachat
        LLM_TRANSPORT_MODE=litellm_gateway
        LITELLM_GATEWAY_URL=http://10.0.0.2:4000
        LITELLM_GATEWAY_API_KEY=super-secret-gateway-key
        GIGACHAT_CLIENT_SECRET=super-secret-gigachat-key
        """,
    )

    result = run_topology_check("--env-file", str(env_file), "--json", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "super-secret" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["environment"]["LITELLM_GATEWAY_API_KEY"] == "[set]"


def test_s1_topology_cli_requires_gateway_url(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path,
        """
        DEPLOYMENT_MODE=offline_intranet
        LLM_PROVIDER=gigachat
        LLM_TRANSPORT_MODE=litellm_gateway
        GIGACHAT_CLIENT_SECRET=secret
        """,
    )

    result = run_topology_check("--env-file", str(env_file), "--require-ready")

    assert result.returncode == 1
    assert "litellm_gateway requires LITELLM_GATEWAY_URL" in result.stdout


def test_s1_env_example_passes_with_placeholders() -> None:
    result = run_topology_check("--allow-placeholders", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "[PASS] LLM topology contract completed" in result.stdout
