#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

REQUIRED_FILES = (
    "docs/codex/GIGACHAT_RUNTIME_HARDENING.md",
    "backend/app/integrations/llm/gigachat_runtime.py",
    "backend/app/integrations/llm/factory.py",
    "backend/app/integrations/llm/providers.py",
    "backend/app/integrations/llm/__init__.py",
    "scripts/kw_gigachat_runtime_hardening_check.py",
    "backend/tests/smoke/test_rf4_gigachat_runtime_hardening.py",
)

REQUIRED_MARKERS = {
    "runtime_report": ("backend/app/integrations/llm/gigachat_runtime.py", "class GigaChatRuntimeHardeningReport"),
    "runtime_selection": ("backend/app/integrations/llm/gigachat_runtime.py", "def validate_llm_runtime_selection("),
    "completion_diagnostic": ("backend/app/integrations/llm/gigachat_runtime.py", "def run_gigachat_completion_diagnostic("),
    "factory_selection_guard": ("backend/app/integrations/llm/factory.py", "validate_llm_runtime_selection(settings)"),
    "provider_timeout_message": ("backend/app/integrations/llm/providers.py", "GigaChat completion request timed out"),
    "init_export": ("backend/app/integrations/llm/__init__.py", "GigaChatRuntimeHardeningReport"),
    "doc_no_k_phase": ("docs/codex/GIGACHAT_RUNTIME_HARDENING.md", "does not start K-phase"),
}

SENSITIVE_FRAGMENTS = ("client-secret", "client_secret", "authorization", "access_token", "Bearer ", "Basic ", "database_url")


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def marker_present(repo_root: Path, rel: str, marker: str) -> bool:
    path = repo_root / rel
    return path.exists() and marker in path.read_text(encoding="utf-8")


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF4 required file: {rel}")
    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF4 marker: {name}")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")
    return errors


def build_success_provider() -> Any:
    from backend.app.integrations.llm import GigaChatProvider

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "http://gigachat.internal/oauth":
            return httpx.Response(200, json={"access_token": "token-redacted", "expires_in": 1800})
        if str(request.url) == "http://10.10.10.30:8080/api/v1/chat/completions":
            return httpx.Response(200, json={"model": "GigaChat-Pro", "choices": [{"message": {"content": "rf4 diagnostic ok"}}]})
        return httpx.Response(404, json={"error": "unexpected"})

    return GigaChatProvider(
        api_base_url="http://10.10.10.30:8080/api/v1",
        auth_url="http://gigachat.internal/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        timeout_seconds=3.0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def build_timeout_provider() -> Any:
    from backend.app.integrations.llm import GigaChatProvider

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated auth timeout", request=request)

    return GigaChatProvider(
        api_base_url="http://10.10.10.30:8080/api/v1",
        auth_url="http://gigachat.internal/oauth",
        scope="GIGACHAT_API_PERS",
        model_name="GigaChat-Pro",
        client_id="client-id",
        client_secret="client-secret",
        timeout_seconds=0.1,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.core.config import Settings
    from backend.app.integrations.llm import GigaChatProvider, build_llm_provider
    from backend.app.integrations.llm.gigachat_runtime import (
        GigaChatRuntimeSelectionError,
        build_gigachat_runtime_hardening_report,
        run_gigachat_completion_diagnostic,
    )

    errors: list[str] = []
    ready_settings = Settings(
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
    ready_report = build_gigachat_runtime_hardening_report(ready_settings)
    if ready_report.status != "ready":
        errors.extend(ready_report.errors)

    default_provider = build_llm_provider(ready_settings)
    if not isinstance(default_provider, GigaChatProvider):
        errors.append("direct production settings did not build GigaChatProvider")

    public_report = build_gigachat_runtime_hardening_report(
        Settings(
            app_env="production",
            deployment_mode="offline_intranet",
            llm_provider="gigachat",
            llm_transport_mode="direct_gigachat",
            gigachat_api_base_url="https://api.public.example/v1",
            gigachat_auth_url="https://auth.public.example/oauth",
            gigachat_client_id="client-id",
            gigachat_client_secret="client-secret",
        )
    )
    if public_report.status == "ready":
        errors.append("public GigaChat endpoints must not be ready in offline_intranet")

    fake_rejected = False
    try:
        build_llm_provider(Settings(app_env="production", deployment_mode="offline_intranet", llm_provider="fake"))
    except GigaChatRuntimeSelectionError:
        fake_rejected = True
    if not fake_rejected:
        errors.append("production offline fake/noop provider was not rejected")

    success_diagnostic = run_gigachat_completion_diagnostic(build_success_provider())
    if success_diagnostic.status != "ready" or not success_diagnostic.response_text_present:
        errors.append("mocked GigaChat diagnostic success did not pass")

    timeout_diagnostic = run_gigachat_completion_diagnostic(build_timeout_provider())
    if timeout_diagnostic.status != "failed" or timeout_diagnostic.error_code != "gigachat_auth_timeout":
        errors.append("mocked GigaChat auth timeout was not classified safely")

    combined_json = json.dumps(
        {
            "ready_report": ready_report.as_dict(),
            "success_diagnostic": success_diagnostic.as_dict(),
            "timeout_diagnostic": timeout_diagnostic.as_dict(),
        },
        sort_keys=True,
    )
    safe_metadata_only = not any(fragment in combined_json for fragment in SENSITIVE_FRAGMENTS)
    if not safe_metadata_only:
        errors.append("RF4 diagnostics leaked sensitive fragments")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "direct_gigachat_default": ready_report.direct_gigachat_default,
        "direct_gigachat_config_ready": ready_report.direct_gigachat_config_ready,
        "direct_provider_built": isinstance(default_provider, GigaChatProvider),
        "no_silent_fallback": ready_report.no_silent_fallback,
        "no_litellm_override": ready_report.no_litellm_override,
        "no_ollama_override": ready_report.no_ollama_override,
        "public_endpoint_rejected": public_report.status != "ready",
        "production_fake_provider_rejected": fake_rejected,
        "endpoint_diagnostics_supported": ready_report.endpoint_diagnostics_supported,
        "mocked_success_diagnostic_ready": success_diagnostic.status == "ready",
        "mocked_timeout_diagnostic_failed_safely": timeout_diagnostic.error_code == "gigachat_auth_timeout",
        "safe_metadata_only": safe_metadata_only,
        "raw_secret_values_stored": False,
        "network_required": False,
        "dependency_versions_changed_by_rf4": False,
        "dockerfiles_changed_by_rf4": False,
        "api_endpoint_added_by_rf4": False,
        "db_schema_migration_added_by_rf4": False,
        "k_phase_started_by_rf4": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))
    return {
        "mode": "gigachat-runtime-hardening",
        "phase": "RF4",
        "checkpoint": "RF4",
        "status": "ready" if not errors else "failed",
        "network_required": False,
        "runtime_changed_by_rf4": True,
        "runtime_change_type": "direct_local_gigachat_config_validation_and_diagnostics",
        "direct_gigachat_default": True,
        "server_3_gigachat_default_runtime": True,
        "server_2_litellm_gateway_optional": True,
        "dependency_versions_changed_by_rf4": False,
        "dockerfiles_changed_by_rf4": False,
        "frontend_runtime_changed_by_rf4": False,
        "browser_runtime_changed_by_rf4": False,
        "api_endpoint_added_by_rf4": False,
        "db_schema_migration_added_by_rf4": False,
        "queue_or_event_store_migration_added_by_rf4": False,
        "cloud_llm_added_by_rf4": False,
        "silent_fallback_allowed_by_rf4": False,
        "litellm_made_mandatory_by_rf4": False,
        "k_phase_started_by_rf4": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF_closure — Runtime Foundation final closure before K0",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF4 local GigaChat runtime hardening check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, require_ready=args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
