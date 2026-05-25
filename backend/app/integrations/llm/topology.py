from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

from backend.app.core.config import Settings

_ALLOWED_TRANSPORT_MODES = {"direct_gigachat", "litellm_gateway"}
_PRIVATE_HOSTS = {"localhost", "127.0.0.1", "::1", "gigachat", "gigachat.local", "gigachat.internal", "litellm", "litellm.local", "litellm.internal"}


@dataclass(frozen=True)
class LLMTopologyContract:
    status: str
    deployment_mode: str
    llm_provider: str
    llm_transport_mode: str
    default_provider: str
    server_roles: dict[str, str]
    endpoints: dict[str, dict[str, object]]
    optional_components: dict[str, bool]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "deployment_mode": self.deployment_mode,
            "llm_provider": self.llm_provider,
            "llm_transport_mode": self.llm_transport_mode,
            "default_provider": self.default_provider,
            "server_roles": self.server_roles,
            "endpoints": self.endpoints,
            "optional_components": self.optional_components,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def build_llm_topology_contract(settings: Settings) -> LLMTopologyContract:
    deployment_mode = settings.deployment_mode.strip().lower()
    provider = settings.llm_provider.strip().lower()
    transport_mode = settings.llm_transport_mode.strip().lower() or "direct_gigachat"

    endpoints = {
        "gigachat_api": _endpoint_summary(settings.gigachat_api_base_url),
        "gigachat_auth": _endpoint_summary(settings.gigachat_auth_url),
        "litellm_gateway": _endpoint_summary(settings.litellm_gateway_url),
    }
    optional_components = {
        "server_2_litellm_gateway": transport_mode == "litellm_gateway" or bool(settings.litellm_gateway_url.strip()),
        "server_2_heavy_runtime_modules": bool(settings.litellm_gateway_url.strip()),
    }

    errors: list[str] = []
    warnings: list[str] = []

    if deployment_mode == "offline_intranet" and provider != "gigachat":
        errors.append("offline_intranet requires LLM_PROVIDER=gigachat")
    if transport_mode not in _ALLOWED_TRANSPORT_MODES:
        errors.append("LLM_TRANSPORT_MODE must be direct_gigachat or litellm_gateway")
    if transport_mode == "direct_gigachat":
        if not settings.gigachat_api_base_url.strip():
            errors.append("direct_gigachat requires GIGACHAT_API_BASE_URL")
        if not settings.gigachat_auth_url.strip():
            errors.append("direct_gigachat requires GIGACHAT_AUTH_URL")
    if transport_mode == "litellm_gateway" and not settings.litellm_gateway_url.strip():
        errors.append("litellm_gateway transport requires LITELLM_GATEWAY_URL")
    for name, summary in endpoints.items():
        if summary["configured"] and not summary["private_or_internal"] and deployment_mode == "offline_intranet":
            warnings.append(f"{name} endpoint does not look private/internal for offline_intranet")

    return LLMTopologyContract(
        status="ready" if not errors else "not_ready",
        deployment_mode=deployment_mode,
        llm_provider=provider,
        llm_transport_mode=transport_mode,
        default_provider="gigachat",
        server_roles={
            "server_1": "KW Studio app, API, frontend, Postgres, artifact storage, workflows",
            "server_2": "Optional LiteLLM-compatible gateway and heavy CPU runtime modules",
            "server_3": "Local GigaChat runtime reachable only by internal ip:port",
        },
        endpoints=endpoints,
        optional_components=optional_components,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _endpoint_summary(value: str) -> dict[str, object]:
    stripped = value.strip()
    if not stripped:
        return {"configured": False, "scheme": "", "host_configured": False, "private_or_internal": False}
    if "CHANGE_ME" in stripped.upper():
        return {"configured": True, "scheme": "placeholder", "host_configured": True, "private_or_internal": True}
    parsed = urlparse(stripped)
    hostname = (parsed.hostname or "").lower()
    return {
        "configured": True,
        "scheme": parsed.scheme,
        "host_configured": bool(hostname),
        "private_or_internal": _is_private_or_internal_host(hostname),
    }


def _is_private_or_internal_host(hostname: str) -> bool:
    if not hostname:
        return False
    if hostname in _PRIVATE_HOSTS:
        return True
    if hostname.endswith(".local") or hostname.endswith(".internal") or hostname.endswith(".lan"):
        return True
    try:
        address = ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local
