from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

from backend.app.core.config import Settings
from backend.app.integrations.llm.models import LLMCompletionRequest
from backend.app.integrations.llm.providers import GigaChatProvider, GigaChatProviderError

GIGACHAT_RUNTIME_HARDENING_WORKFLOW_ID = "llm.gigachat_runtime_hardening"
GIGACHAT_DIRECT_TRANSPORT = "direct_gigachat"
GIGACHAT_PROVIDER = "gigachat"
PRIVATE_OR_INTERNAL_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "gigachat",
    "gigachat.local",
    "gigachat.internal",
}
SENSITIVE_FIELD_NAMES = {
    "client_secret",
    "gigachat_client_secret",
    "api_key",
    "authorization",
    "token",
    "access_token",
    "database_url",
    "password",
}
PLACEHOLDER_MARKERS = ("CHANGE_ME", "CHANGEME", "REPLACE_ME", "TODO", "YOUR_")


@dataclass(frozen=True)
class GigaChatEndpointRuntimeSummary:
    configured: bool
    scheme: str
    host_configured: bool
    private_or_internal: bool
    placeholder: bool
    normalized_url: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GigaChatRuntimeHardeningReport:
    status: str
    workflow_id: str
    deployment_mode: str
    app_env: str
    llm_provider: str
    llm_transport_mode: str
    direct_gigachat_default: bool
    direct_gigachat_config_ready: bool
    no_silent_fallback: bool
    no_litellm_override: bool
    no_ollama_override: bool
    no_public_internet_runtime: bool
    endpoint_diagnostics_supported: bool
    timeout_seconds: float
    timeout_configured: bool
    credentials_configured: bool
    endpoints: dict[str, dict[str, object]]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "workflow_id": self.workflow_id,
            "deployment_mode": self.deployment_mode,
            "app_env": self.app_env,
            "llm_provider": self.llm_provider,
            "llm_transport_mode": self.llm_transport_mode,
            "direct_gigachat_default": self.direct_gigachat_default,
            "direct_gigachat_config_ready": self.direct_gigachat_config_ready,
            "no_silent_fallback": self.no_silent_fallback,
            "no_litellm_override": self.no_litellm_override,
            "no_ollama_override": self.no_ollama_override,
            "no_public_internet_runtime": self.no_public_internet_runtime,
            "endpoint_diagnostics_supported": self.endpoint_diagnostics_supported,
            "timeout_seconds": self.timeout_seconds,
            "timeout_configured": self.timeout_configured,
            "credentials_configured": self.credentials_configured,
            "endpoints": self.endpoints,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "safe_metadata": self.safe_metadata,
        }


@dataclass(frozen=True)
class GigaChatDiagnosticResult:
    status: str
    provider: str
    model: str
    endpoint_probe_attempted: bool
    completion_probe_supported: bool
    response_text_present: bool
    error_code: str | None
    operator_message: str
    raw_exception_stored: bool
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class GigaChatRuntimeSelectionError(ValueError):
    """Raised when offline/intranet LLM runtime selection violates RF4 policy."""


def validate_llm_runtime_selection(settings: Settings) -> None:
    # Preserve development/test ergonomics: provider construction may happen with
    # placeholder or empty endpoints, while runtime calls still validate credentials.
    # RF4 strict no-silent-fallback policy applies to production offline/intranet.
    if settings.app_env.strip().lower() in {"development", "test"}:
        return
    report = build_gigachat_runtime_hardening_report(settings, require_credentials=False, allow_placeholders=True)
    if report.errors:
        raise GigaChatRuntimeSelectionError("; ".join(report.errors))


def build_gigachat_runtime_hardening_report(
    settings: Settings,
    *,
    require_credentials: bool = True,
    allow_placeholders: bool = False,
) -> GigaChatRuntimeHardeningReport:
    deployment_mode = settings.deployment_mode.strip().lower()
    app_env = settings.app_env.strip().lower()
    provider = settings.llm_provider.strip().lower()
    transport = settings.llm_transport_mode.strip().lower() or GIGACHAT_DIRECT_TRANSPORT

    endpoints = {
        "gigachat_api": endpoint_runtime_summary(settings.gigachat_api_base_url, allow_placeholders=allow_placeholders).as_dict(),
        "gigachat_auth": endpoint_runtime_summary(settings.gigachat_auth_url, allow_placeholders=allow_placeholders).as_dict(),
        "litellm_gateway": endpoint_runtime_summary(settings.litellm_gateway_url, allow_placeholders=allow_placeholders).as_dict(),
        "ollama": endpoint_runtime_summary(settings.ollama_api_base_url, allow_placeholders=allow_placeholders).as_dict(),
    }
    credentials_configured = bool(settings.gigachat_client_id.strip() and settings.gigachat_client_secret.strip())
    timeout_configured = settings.gigachat_timeout_seconds > 0
    direct_mode = provider == GIGACHAT_PROVIDER and transport == GIGACHAT_DIRECT_TRANSPORT
    errors: list[str] = []
    warnings: list[str] = []

    if deployment_mode == "offline_intranet" and provider != GIGACHAT_PROVIDER:
        if provider in {"fake", "noop"} and app_env in {"development", "test"}:
            warnings.append("fake/noop LLM provider is allowed only in development/test")
        else:
            errors.append("offline_intranet production runtime requires LLM_PROVIDER=gigachat")
    if provider == GIGACHAT_PROVIDER and transport not in {GIGACHAT_DIRECT_TRANSPORT, "litellm_gateway"}:
        errors.append("LLM_TRANSPORT_MODE must be direct_gigachat or litellm_gateway")
    if deployment_mode == "offline_intranet" and provider == GIGACHAT_PROVIDER and transport != GIGACHAT_DIRECT_TRANSPORT:
        warnings.append("direct_gigachat remains the production default; LiteLLM is explicit optional transport only")
    if direct_mode:
        if not settings.gigachat_api_base_url.strip():
            errors.append("direct_gigachat requires GIGACHAT_API_BASE_URL")
        if not settings.gigachat_auth_url.strip():
            errors.append("direct_gigachat requires GIGACHAT_AUTH_URL")
        if require_credentials and not credentials_configured:
            errors.append("direct_gigachat requires configured GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET")
    if provider == GIGACHAT_PROVIDER and transport == "litellm_gateway" and not settings.litellm_gateway_url.strip():
        errors.append("litellm_gateway transport requires LITELLM_GATEWAY_URL")

    active_runtime_endpoint_names = _active_runtime_endpoint_names(provider, transport)
    if deployment_mode == "offline_intranet":
        for name in active_runtime_endpoint_names:
            summary = endpoints[name]
            if summary["configured"] and not summary["private_or_internal"]:
                errors.append(f"{name} endpoint must be private/internal for offline_intranet")
    if not timeout_configured:
        errors.append("GIGACHAT_TIMEOUT_SECONDS must be greater than zero")
    if settings.ollama_api_base_url.strip() and app_env not in {"development", "test"}:
        warnings.append("Ollama endpoint configured outside development/test; Ollama remains fallback/dev only")

    no_litellm_override = not (provider == GIGACHAT_PROVIDER and transport == "litellm_gateway")
    no_ollama_override = provider != "ollama"
    no_public_runtime = not any(
        endpoints[name]["configured"] and not endpoints[name]["private_or_internal"]
        for name in active_runtime_endpoint_names
    )
    config_ready = direct_mode and timeout_configured and bool(settings.gigachat_api_base_url.strip()) and bool(settings.gigachat_auth_url.strip())
    if require_credentials:
        config_ready = config_ready and credentials_configured

    safe_metadata = {
        "workflow_id": GIGACHAT_RUNTIME_HARDENING_WORKFLOW_ID,
        "schema_version": "gigachat_runtime_hardening.v1",
        "runtime_changed_by_rf4": True,
        "runtime_change_type": "direct_local_gigachat_config_validation_and_diagnostics",
        "direct_gigachat_default": True,
        "default_production_llm": "gigachat",
        "default_transport_mode": GIGACHAT_DIRECT_TRANSPORT,
        "server_3_gigachat_runtime_required": True,
        "server_2_litellm_gateway_optional": True,
        "no_silent_fallback": True,
        "no_litellm_override": no_litellm_override,
        "no_ollama_override": no_ollama_override,
        "no_public_internet_runtime": no_public_runtime,
        "endpoint_diagnostics_supported": True,
        "timeout_configured": timeout_configured,
        "credentials_configured": credentials_configured,
        "credentials_redacted": True,
        "raw_secret_values_stored": False,
        "dependency_versions_changed_by_rf4": False,
        "dockerfiles_changed_by_rf4": False,
        "api_endpoint_added_by_rf4": False,
        "db_schema_migration_added_by_rf4": False,
        "k_phase_started_by_rf4": False,
    }

    return GigaChatRuntimeHardeningReport(
        status="ready" if not errors else "not_ready",
        workflow_id=GIGACHAT_RUNTIME_HARDENING_WORKFLOW_ID,
        deployment_mode=deployment_mode,
        app_env=app_env,
        llm_provider=provider,
        llm_transport_mode=transport,
        direct_gigachat_default=True,
        direct_gigachat_config_ready=config_ready,
        no_silent_fallback=True,
        no_litellm_override=no_litellm_override,
        no_ollama_override=no_ollama_override,
        no_public_internet_runtime=no_public_runtime,
        endpoint_diagnostics_supported=True,
        timeout_seconds=settings.gigachat_timeout_seconds,
        timeout_configured=timeout_configured,
        credentials_configured=credentials_configured,
        endpoints=endpoints,
        errors=tuple(errors),
        warnings=tuple(warnings),
        safe_metadata=safe_metadata,
    )


def run_gigachat_completion_diagnostic(
    provider: GigaChatProvider,
    *,
    prompt: str = "RF4 GigaChat diagnostic ping.",
) -> GigaChatDiagnosticResult:
    try:
        result = provider.complete(LLMCompletionRequest(prompt=prompt, temperature=0.0))
    except GigaChatProviderError as exc:
        return _diagnostic_failure(provider, error_code=_classify_gigachat_error(exc), message=_operator_message_for_error(exc))
    except Exception as exc:  # pragma: no cover - deliberately defensive operator boundary
        return _diagnostic_failure(provider, error_code="gigachat_unexpected_error", message=_safe_operator_message(str(exc)))

    return GigaChatDiagnosticResult(
        status="ready",
        provider=provider.provider_name,
        model=provider.model_name,
        endpoint_probe_attempted=True,
        completion_probe_supported=True,
        response_text_present=bool(result.text.strip()),
        error_code=None,
        operator_message="GigaChat completion diagnostic succeeded.",
        raw_exception_stored=False,
        safe_metadata={
            "workflow_id": GIGACHAT_RUNTIME_HARDENING_WORKFLOW_ID,
            "diagnostic_type": "completion_probe",
            "provider": provider.provider_name,
            "model": provider.model_name,
            "status": "ready",
            "endpoint_probe_attempted": True,
            "response_text_present": bool(result.text.strip()),
            "raw_exception_stored": False,
            "raw_secret_values_stored": False,
        },
    )



def _active_runtime_endpoint_names(provider: str, transport: str) -> tuple[str, ...]:
    if provider == GIGACHAT_PROVIDER and transport == GIGACHAT_DIRECT_TRANSPORT:
        return ("gigachat_api", "gigachat_auth")
    if provider == GIGACHAT_PROVIDER and transport == "litellm_gateway":
        return ("litellm_gateway",)
    if provider == "ollama":
        return ("ollama",)
    return ()

def endpoint_runtime_summary(value: str, *, allow_placeholders: bool) -> GigaChatEndpointRuntimeSummary:
    stripped = value.strip()
    if not stripped:
        return GigaChatEndpointRuntimeSummary(False, "", False, False, False, "")
    placeholder = _has_placeholder(stripped)
    if allow_placeholders and placeholder:
        return GigaChatEndpointRuntimeSummary(True, "placeholder", True, True, True, "placeholder://redacted")
    parsed = urlparse(stripped)
    hostname = (parsed.hostname or "").lower()
    normalized = f"{parsed.scheme}://{hostname}"
    if parsed.port is not None:
        normalized = f"{normalized}:{parsed.port}"
    return GigaChatEndpointRuntimeSummary(
        configured=True,
        scheme=parsed.scheme,
        host_configured=bool(hostname),
        private_or_internal=_is_private_or_internal_host(hostname),
        placeholder=placeholder,
        normalized_url=normalized,
    )


def _diagnostic_failure(provider: GigaChatProvider, *, error_code: str, message: str) -> GigaChatDiagnosticResult:
    return GigaChatDiagnosticResult(
        status="failed",
        provider=provider.provider_name,
        model=provider.model_name,
        endpoint_probe_attempted=True,
        completion_probe_supported=True,
        response_text_present=False,
        error_code=error_code,
        operator_message=message,
        raw_exception_stored=False,
        safe_metadata={
            "workflow_id": GIGACHAT_RUNTIME_HARDENING_WORKFLOW_ID,
            "diagnostic_type": "completion_probe",
            "provider": provider.provider_name,
            "model": provider.model_name,
            "status": "failed",
            "error_code": error_code,
            "endpoint_probe_attempted": True,
            "response_text_present": False,
            "raw_exception_stored": False,
            "raw_secret_values_stored": False,
        },
    )


def _classify_gigachat_error(exc: GigaChatProviderError) -> str:
    text = str(exc).lower()
    cause = exc.__cause__
    cause_name = type(cause).__name__.lower() if cause is not None else ""
    if "timeout" in text or "timeout" in cause_name:
        if "oauth" in text or "token" in text:
            return "gigachat_auth_timeout"
        return "gigachat_completion_timeout"
    if "oauth" in text or "token" in text:
        return "gigachat_auth_failed"
    return "gigachat_completion_failed"


def _operator_message_for_error(exc: GigaChatProviderError) -> str:
    error_code = _classify_gigachat_error(exc)
    if error_code == "gigachat_auth_timeout":
        return "GigaChat OAuth endpoint did not respond before the configured timeout. Check Server 3 auth reachability and timeout settings."
    if error_code == "gigachat_completion_timeout":
        return "GigaChat completion endpoint did not respond before the configured timeout. Check Server 3 runtime reachability and timeout settings."
    if error_code == "gigachat_auth_failed":
        return "GigaChat OAuth request failed. Check local credentials, scope, and Server 3 auth endpoint."
    return "GigaChat completion request failed. Check Server 3 runtime endpoint, model name, and local network reachability."


def _safe_operator_message(text: str) -> str:
    for marker in ("client_secret", "authorization", "access_token", "token", "password", "database_url"):
        text = text.replace(marker, "[redacted]")
    return text[:240]


def _has_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def _is_private_or_internal_host(hostname: str) -> bool:
    if not hostname:
        return False
    if hostname in PRIVATE_OR_INTERNAL_HOSTS:
        return True
    if hostname.endswith(".local") or hostname.endswith(".internal") or hostname.endswith(".lan"):
        return True
    try:
        address = ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local
