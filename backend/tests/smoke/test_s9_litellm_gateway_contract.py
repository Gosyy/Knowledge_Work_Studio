from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_litellm_gateway_check.py"
CONTRACT_PATH = REPO_ROOT / "backend" / "app" / "integrations" / "llm" / "litellm_gateway_contract.py"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("kw_s9_litellm_gateway_contract_test", CONTRACT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contract = load_contract_module()
build_litellm_gateway_manifest = contract.build_litellm_gateway_manifest
validate_litellm_gateway_manifest = contract.validate_litellm_gateway_manifest


def base_values() -> dict[str, str]:
    return {
        "APP_ENV": "production",
        "DEPLOYMENT_MODE": "offline_intranet",
        "LLM_PROVIDER": "gigachat",
        "LLM_TRANSPORT_MODE": "direct_gigachat",
        "GIGACHAT_API_BASE_URL": "http://server3.internal:8080",
        "GIGACHAT_AUTH_URL": "http://server3.internal:8081",
        "GIGACHAT_CLIENT_ID": "client",
        "GIGACHAT_CLIENT_SECRET": "secret-value",
    }


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_s9_direct_gigachat_contract_is_ready() -> None:
    manifest = build_litellm_gateway_manifest(base_values())

    assert manifest["status"] == "ready"
    assert manifest["default_provider"] == "gigachat"
    assert manifest["selected_transport"] == "direct_gigachat"
    assert manifest["gateway"]["optional"] is True
    assert manifest["gateway"]["may_replace_gigachat_provider"] is False
    assert validate_litellm_gateway_manifest(manifest) == []


def test_s9_litellm_gateway_contract_is_ready_for_internal_server2_url() -> None:
    values = base_values()
    values.update(
        {
            "LLM_TRANSPORT_MODE": "litellm_gateway",
            "LITELLM_GATEWAY_URL": "http://server2.internal:4000",
            "LITELLM_GATEWAY_MODEL": "gigachat-local",
            "LITELLM_GATEWAY_API_KEY": "super-secret-key",
        }
    )

    manifest = build_litellm_gateway_manifest(values)

    assert manifest["status"] == "ready"
    assert manifest["selected_transport"] == "litellm_gateway"
    assert manifest["gateway"]["transport_only"] is True
    assert manifest["gateway"]["endpoint"]["private_or_internal"] is True
    assert manifest["environment"]["LITELLM_GATEWAY_API_KEY"] == "[set]"
    assert "super-secret-key" not in json.dumps(manifest)


def test_s9_rejects_litellm_as_provider_replacement() -> None:
    values = base_values()
    values["LLM_PROVIDER"] = "litellm"

    manifest = build_litellm_gateway_manifest(values)

    assert manifest["status"] == "not_ready"
    assert "offline_intranet requires LLM_PROVIDER=gigachat; LiteLLM is a gateway, not provider replacement" in manifest["errors"]


def test_s9_rejects_public_litellm_gateway_url_for_offline_intranet() -> None:
    values = base_values()
    values.update(
        {
            "LLM_TRANSPORT_MODE": "litellm_gateway",
            "LITELLM_GATEWAY_URL": "https://example.com/v1",
            "LITELLM_GATEWAY_MODEL": "gigachat-local",
        }
    )

    manifest = build_litellm_gateway_manifest(values)

    assert manifest["status"] == "not_ready"
    assert "litellm_gateway LITELLM_GATEWAY_URL must be private/internal for offline_intranet" in manifest["errors"]


def test_s9_rejects_missing_gateway_model_when_gateway_selected() -> None:
    values = base_values()
    values.update({"LLM_TRANSPORT_MODE": "litellm_gateway", "LITELLM_GATEWAY_URL": "http://server2.internal:4000"})

    manifest = build_litellm_gateway_manifest(values)

    assert manifest["status"] == "not_ready"
    assert "litellm_gateway requires LITELLM_GATEWAY_MODEL" in manifest["errors"]


def test_s9_cli_accepts_env_deploy_example_without_network_probe() -> None:
    result = run_check("--allow-placeholders", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "[PASS] LiteLLM gateway optional transport contract completed" in result.stdout
    assert "probe" not in result.stderr.lower()


def test_s9_cli_accepts_internal_litellm_gateway_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.s9"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DEPLOYMENT_MODE=offline_intranet",
                "LLM_PROVIDER=gigachat",
                "LLM_TRANSPORT_MODE=litellm_gateway",
                "GIGACHAT_API_BASE_URL=http://server3.internal:8080",
                "GIGACHAT_AUTH_URL=http://server3.internal:8081",
                "LITELLM_GATEWAY_URL=http://server2.internal:4000",
                "LITELLM_GATEWAY_MODEL=gigachat-local",
                "LITELLM_GATEWAY_API_KEY=secret-value",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check("--env-file", str(env_file), "--mode", "litellm_gateway", "--json", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    manifest = json.loads(result.stdout)
    assert manifest["status"] == "ready"
    assert manifest["selected_transport"] == "litellm_gateway"
    assert manifest["environment"]["LITELLM_GATEWAY_API_KEY"] == "[set]"
    assert "secret-value" not in result.stdout


def test_s9_cli_fails_closed_for_network_probe() -> None:
    result = run_check("--allow-placeholders", "--probe-endpoint")

    assert result.returncode == 2
    assert "--probe-endpoint is intentionally not implemented" in result.stdout


def test_s9_production_gate_contains_litellm_gateway_check() -> None:
    gate = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "scripts/kw_litellm_gateway_check.py" in gate
    assert "LiteLLM gateway optional transport contract" in gate
    assert "docs/litellm-gateway-topology.md" in gate
    assert "docs/heavy-node-runtime.md" in gate
