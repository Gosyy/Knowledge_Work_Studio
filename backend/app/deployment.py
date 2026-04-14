from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.core.config import Settings

_ALLOWED_STORAGE_BACKENDS = {"local", "remote_object_storage", "minio", "s3"}
_APPROVED_DEPLOYMENT_MODE = "offline_intranet"
_APPROVED_METADATA_BACKEND = "postgres"
_APPROVED_LLM_PROVIDER = "gigachat"


@dataclass(frozen=True)
class DeploymentReadiness:
    status: str
    deployment_mode: str
    metadata_backend: str
    storage_backend: str
    llm_provider: str
    checks: dict[str, bool]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "deployment_mode": self.deployment_mode,
            "metadata_backend": self.metadata_backend,
            "storage_backend": self.storage_backend,
            "llm_provider": self.llm_provider,
            "checks": self.checks,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _normalized(value: str) -> str:
    return value.strip().lower()


def _is_set(value: str) -> bool:
    return bool(value and value.strip())


def _is_postgres_dsn(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized.startswith("postgresql://") or normalized.startswith("postgresql+psycopg://")


def build_deployment_readiness(settings: Settings) -> DeploymentReadiness:
    deployment_mode = _normalized(settings.deployment_mode)
    metadata_backend = _normalized(settings.metadata_backend)
    storage_backend = _normalized(settings.storage_backend)
    llm_provider = _normalized(settings.llm_provider)

    checks: dict[str, bool] = {
        "offline_intranet_mode": deployment_mode == _APPROVED_DEPLOYMENT_MODE,
        "postgres_metadata_truth": metadata_backend == _APPROVED_METADATA_BACKEND,
        "sqlite_not_runtime_truth": not settings.sqlite_runtime_allowed,
        "postgres_dsn_configured": _is_postgres_dsn(settings.database_url),
        "storage_backend_supported": storage_backend in _ALLOWED_STORAGE_BACKENDS,
        "llm_provider_gigachat_only": llm_provider == _APPROVED_LLM_PROVIDER,
        "gigachat_urls_configured": _is_set(settings.gigachat_api_base_url)
        and _is_set(settings.gigachat_auth_url),
        "gigachat_credentials_configured": _is_set(settings.gigachat_client_id)
        and _is_set(settings.gigachat_client_secret),
        "secret_key_configured": _is_set(settings.secret_key)
        and settings.secret_key != "change-me"
        and len(settings.secret_key) >= 16,
    }

    storage_configured = False
    warnings: list[str] = []
    if storage_backend == "local":
        storage_configured = _is_set(settings.storage_root)
        warnings.append(
            "Local storage is acceptable for offline intranet only when STORAGE_ROOT "
            "points to approved internal disk, NAS, or a mounted remote storage volume."
        )
    elif storage_backend in _ALLOWED_STORAGE_BACKENDS:
        storage_configured = _is_set(settings.storage_endpoint) and _is_set(settings.storage_bucket)
        if storage_backend in {"minio", "s3"}:
            storage_configured = (
                storage_configured
                and _is_set(settings.storage_access_key)
                and _is_set(settings.storage_secret_key)
            )
        warnings.append(
            "Remote object storage configuration is validated here, but object-storage "
            "I/O must be backed by a real adapter before production use."
        )
    checks["storage_configured"] = storage_configured

    errors: list[str] = []
    if not checks["offline_intranet_mode"]:
        errors.append("DEPLOYMENT_MODE must be offline_intranet.")
    if not checks["postgres_metadata_truth"]:
        errors.append("METADATA_BACKEND must be postgres in the approved deployment profile.")
    if not checks["sqlite_not_runtime_truth"]:
        errors.append("SQLITE_RUNTIME_ALLOWED must remain false outside tests/development.")
    if not checks["postgres_dsn_configured"]:
        errors.append("DATABASE_URL must be a Postgres DSN.")
    if not checks["storage_backend_supported"]:
        errors.append(
            "STORAGE_BACKEND must be one of: "
            + ", ".join(sorted(_ALLOWED_STORAGE_BACKENDS))
            + "."
        )
    if not checks["storage_configured"]:
        errors.append("Storage backend settings are incomplete.")
    if not checks["llm_provider_gigachat_only"]:
        errors.append("LLM_PROVIDER must be gigachat in the approved deployment profile.")
    if not checks["gigachat_urls_configured"]:
        errors.append("GigaChat API/auth URLs must be configured, preferably via an internal gateway.")
    if not checks["gigachat_credentials_configured"]:
        errors.append("GigaChat client credentials must be configured through secrets.")
    if not checks["secret_key_configured"]:
        errors.append("SECRET_KEY must be a non-default secret with at least 16 characters.")

    return DeploymentReadiness(
        status="ready" if not errors else "not_ready",
        deployment_mode=deployment_mode,
        metadata_backend=metadata_backend,
        storage_backend=storage_backend,
        llm_provider=llm_provider,
        checks=checks,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
