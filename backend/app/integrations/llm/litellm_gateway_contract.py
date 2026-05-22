from __future__ import annotations

import shlex
from dataclasses import asdict, dataclass
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "litellm_gateway_contract.v1"
WORKFLOW_ID = "llm_provider"
DEFAULT_PROVIDER = "gigachat"
ALLOWED_TRANSPORT_MODES = ("direct_gigachat", "litellm_gateway")
SENSITIVE_KEY_PARTS = ("SECRET", "PASSWORD", "TOKEN", "ACCESS_KEY", "API_KEY", "CLIENT_SECRET", "DATABASE_URL")
PLACEHOLDER_MARKERS = ("CHANGE_ME", "CHANGEME", "REPLACE_ME", "TODO", "YOUR_")

ENV_KEYS = (
    "APP_ENV",
    "DEPLOYMENT_MODE",
    "LLM_PROVIDER",
    "LLM_TRANSPORT_MODE",
    "GIGACHAT_API_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_MODEL",
    "GIGACHAT_RUNTIME_MODE",
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
    "LITELLM_GATEWAY_URL",
    "LITELLM_GATEWAY_MODEL",
    "LITELLM_GATEWAY_API_KEY",
    "OLLAMA_API_BASE_URL",
    "OLLAMA_MODEL",
)


@dataclass(frozen=True)
class EndpointSummary:
    configured: bool
    scheme: str
    host_configured: bool
    private_or_internal: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        try:
            tokens = shlex.split(line, comments=False, posix=True)
        except ValueError:
            tokens = line.split()
        if not tokens and "=" in line:
            tokens = [line]
        for token in tokens:
            if token.startswith("export "):
                token = token[len("export ") :]
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            key = key.strip()
            if key in ENV_KEYS:
                values[key] = value.strip().strip('"').strip("'")
    return values


def read_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    return parse_env_text(path.read_text(encoding="utf-8"))


def merged_values(env_file_values: dict[str, str], environ: dict[str, str] | None = None) -> dict[str, str]:
    env = environ if environ is not None else {}
    values = dict(env_file_values)
    for key in ENV_KEYS:
        if key in env:
            values[key] = env.get(key, "")
    values.setdefault("APP_ENV", "production")
    values.setdefault("DEPLOYMENT_MODE", "offline_intranet")
    values.setdefault("LLM_PROVIDER", DEFAULT_PROVIDER)
    values.setdefault("LLM_TRANSPORT_MODE", "direct_gigachat")
    return values


def is_sensitive_key(key: str) -> bool:
    return any(part in key.upper() for part in SENSITIVE_KEY_PARTS)


def redact(key: str, value: str | None) -> str:
    if is_sensitive_key(key):
        return "[set]" if value and value.strip() else "[unset]"
    return value or ""


def redacted_values(values: dict[str, str]) -> dict[str, str]:
    return {key: redact(key, values.get(key, "")) for key in ENV_KEYS if key in values}


def has_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def is_private_or_internal_host(hostname: str) -> bool:
    if not hostname:
        return False
    host = hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1", "gigachat", "litellm", "litellm-gateway"}:
        return True
    if host.endswith(".local") or host.endswith(".internal") or host.endswith(".lan"):
        return True
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def endpoint_summary(value: str, *, allow_placeholders: bool) -> EndpointSummary:
    stripped = value.strip()
    if not stripped:
        return EndpointSummary(False, "", False, False)
    if allow_placeholders and has_placeholder(stripped):
        return EndpointSummary(True, "placeholder", True, True)
    parsed = urlparse(stripped)
    hostname = parsed.hostname or ""
    return EndpointSummary(True, parsed.scheme, bool(hostname), is_private_or_internal_host(hostname))


def _required_selected_endpoint(
    *,
    errors: list[str],
    endpoint_name: str,
    env_key: str,
    value: str,
    summary: EndpointSummary,
    offline_intranet: bool,
) -> None:
    if not value.strip():
        errors.append(f"{endpoint_name} requires {env_key}")
        return
    if not summary.host_configured:
        errors.append(f"{endpoint_name} {env_key} must include a host")
    if offline_intranet and not summary.private_or_internal:
        errors.append(f"{endpoint_name} {env_key} must be private/internal for offline_intranet")


def build_litellm_gateway_manifest(
    values: dict[str, str],
    *,
    allow_placeholders: bool = False,
    mode: str = "configured",
) -> dict[str, Any]:
    deployment_mode = values.get("DEPLOYMENT_MODE", "offline_intranet").strip().lower()
    app_env = values.get("APP_ENV", "production").strip().lower()
    runtime_mode = values.get("GIGACHAT_RUNTIME_MODE", "offline_intranet").strip().lower() or "offline_intranet"
    public_internet_test_mode = runtime_mode == "public_internet_test"
    offline_endpoint_guard = deployment_mode == "offline_intranet" and not public_internet_test_mode
    provider = values.get("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    transport = values.get("LLM_TRANSPORT_MODE", "direct_gigachat").strip().lower() or "direct_gigachat"
    offline_intranet = deployment_mode == "offline_intranet"

    endpoints = {
        "gigachat_api": endpoint_summary(values.get("GIGACHAT_API_BASE_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
        "gigachat_auth": endpoint_summary(values.get("GIGACHAT_AUTH_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
        "litellm_gateway": endpoint_summary(values.get("LITELLM_GATEWAY_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
        "ollama": endpoint_summary(values.get("OLLAMA_API_BASE_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
    }

    errors: list[str] = []
    warnings: list[str] = []
    if runtime_mode not in {"offline_intranet", "public_internet_test"}:
        errors.append("unsupported GIGACHAT_RUNTIME_MODE; use offline_intranet or public_internet_test")
    if public_internet_test_mode:
        if provider != DEFAULT_PROVIDER or transport != "direct_gigachat":
            errors.append("public_internet_test requires LLM_PROVIDER=gigachat and LLM_TRANSPORT_MODE=direct_gigachat")
        warnings.append("public_internet_test is for operator internet tests only and is not offline/intranet proof")

    if provider != DEFAULT_PROVIDER:
        errors.append("offline_intranet requires LLM_PROVIDER=gigachat; LiteLLM is a gateway, not provider replacement")

    if transport not in ALLOWED_TRANSPORT_MODES:
        errors.append("LLM_TRANSPORT_MODE must be direct_gigachat or litellm_gateway")

    if transport == "direct_gigachat":
        _required_selected_endpoint(
            errors=errors,
            endpoint_name="direct_gigachat",
            env_key="GIGACHAT_API_BASE_URL",
            value=values.get("GIGACHAT_API_BASE_URL", ""),
            summary=endpoint_summary(values.get("GIGACHAT_API_BASE_URL", ""), allow_placeholders=allow_placeholders),
            offline_intranet=offline_endpoint_guard,
        )
        _required_selected_endpoint(
            errors=errors,
            endpoint_name="direct_gigachat",
            env_key="GIGACHAT_AUTH_URL",
            value=values.get("GIGACHAT_AUTH_URL", ""),
            summary=endpoint_summary(values.get("GIGACHAT_AUTH_URL", ""), allow_placeholders=allow_placeholders),
            offline_intranet=offline_endpoint_guard,
        )

    if transport == "litellm_gateway":
        _required_selected_endpoint(
            errors=errors,
            endpoint_name="litellm_gateway",
            env_key="LITELLM_GATEWAY_URL",
            value=values.get("LITELLM_GATEWAY_URL", ""),
            summary=endpoint_summary(values.get("LITELLM_GATEWAY_URL", ""), allow_placeholders=allow_placeholders),
            offline_intranet=offline_endpoint_guard,
        )
        if not values.get("LITELLM_GATEWAY_MODEL", "").strip():
            errors.append("litellm_gateway requires LITELLM_GATEWAY_MODEL")
        if not values.get("GIGACHAT_API_BASE_URL", "").strip() and not allow_placeholders:
            warnings.append("litellm_gateway should route to local GigaChat behind Server 2; direct GigaChat endpoint is not configured")

    if values.get("LITELLM_GATEWAY_URL", "").strip() and transport != "litellm_gateway":
        warnings.append("LITELLM_GATEWAY_URL is configured but LLM_TRANSPORT_MODE is not litellm_gateway")

    if values.get("OLLAMA_API_BASE_URL", "").strip() and app_env not in {"development", "test"}:
        warnings.append("OLLAMA is fallback/dev only and must not become production default")

    return {
        "schema_version": SCHEMA_VERSION,
        "workflow_id": WORKFLOW_ID,
        "status": "ready" if not errors else "not_ready",
        "mode": mode,
        "deployment_mode": deployment_mode,
        "gigachat_runtime_mode": runtime_mode,
        "public_internet_test_mode": public_internet_test_mode,
        "public_internet_test_is_offline_proof": False,
        "default_provider": DEFAULT_PROVIDER,
        "selected_provider": provider,
        "selected_transport": transport,
        "allowed_transport_modes": list(ALLOWED_TRANSPORT_MODES),
        "server_roles": {
            "server_1": "KW Studio app, backend, frontend, Postgres, artifact storage, workflows",
            "server_2": "Optional LiteLLM-compatible gateway and heavy CPU runtime modules",
            "server_3": "Local GigaChat runtime reachable only by internal ip:port",
        },
        "gateway": {
            "server": "server_2",
            "optional": True,
            "transport_only": True,
            "may_replace_gigachat_provider": False,
            "network_policy": "offline_intranet_internal_only",
            "endpoint": endpoints["litellm_gateway"],
        },
        "heavy_node": {
            "server": "server_2",
            "optional": True,
            "modules": ["embeddings", "ocr", "rerank", "heavy_cpu_workflows"],
            "may_be_required_for_core_app_startup": False,
        },
        "controls": {
            "direct_gigachat_remains_first_class": True,
            "litellm_gateway_is_optional": True,
            "ollama_is_dev_fallback_only": True,
            "no_network_probe_by_default": True,
            "secrets_redacted": True,
            "offline_intranet_required": offline_intranet,
        },
        "endpoints": endpoints,
        "environment": redacted_values(values),
        "errors": errors,
        "warnings": warnings,
    }


def validate_litellm_gateway_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be litellm_gateway_contract.v1")
    if manifest.get("workflow_id") != WORKFLOW_ID:
        errors.append("workflow_id must be llm_provider")
    if manifest.get("default_provider") != DEFAULT_PROVIDER:
        errors.append("default_provider must remain gigachat")
    if manifest.get("gateway", {}).get("transport_only") is not True:
        errors.append("LiteLLM gateway must be transport_only")
    if manifest.get("gateway", {}).get("may_replace_gigachat_provider") is not False:
        errors.append("LiteLLM gateway must not replace GigaChat provider")
    if manifest.get("controls", {}).get("no_network_probe_by_default") is not True:
        errors.append("S9 must not require network probing by default")
    if manifest.get("errors"):
        errors.extend(str(error) for error in manifest.get("errors", []))
    return errors
