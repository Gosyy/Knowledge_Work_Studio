#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse

SENSITIVE_KEY_PARTS = ("SECRET", "PASSWORD", "TOKEN", "ACCESS_KEY", "API_KEY", "CLIENT_SECRET", "DATABASE_URL")
PLACEHOLDER_MARKERS = ("CHANGE_ME", "CHANGEME", "REPLACE_ME", "TODO", "YOUR_")
TRANSPORT_MODES = {"direct_gigachat", "litellm_gateway"}
ENV_KEYS = (
    "APP_ENV",
    "DEPLOYMENT_MODE",
    "LLM_PROVIDER",
    "LLM_TRANSPORT_MODE",
    "GIGACHAT_API_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_MODEL",
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
    "LITELLM_GATEWAY_URL",
    "LITELLM_GATEWAY_MODEL",
    "LITELLM_GATEWAY_API_KEY",
)


@dataclass(frozen=True)
class EndpointSummary:
    configured: bool
    scheme: str
    host_configured: bool
    private_or_internal: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "configured": self.configured,
            "scheme": self.scheme,
            "host_configured": self.host_configured,
            "private_or_internal": self.private_or_internal,
        }


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


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
            if key.strip() in ENV_KEYS:
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    return parse_env_text(path.read_text(encoding="utf-8"))


def select_env_file(repo_root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    deploy = repo_root / ".env.deploy"
    if deploy.exists():
        return deploy
    example = repo_root / ".env.deploy.example"
    if example.exists():
        return example
    return None


def merged_values(env_file_values: dict[str, str]) -> dict[str, str]:
    values = dict(env_file_values)
    for key in ENV_KEYS:
        if os.getenv(key) is not None:
            values[key] = os.getenv(key, "")
    values.setdefault("APP_ENV", "production")
    values.setdefault("DEPLOYMENT_MODE", "offline_intranet")
    values.setdefault("LLM_PROVIDER", "gigachat")
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


def endpoint_summary(value: str, *, allow_placeholders: bool) -> EndpointSummary:
    stripped = value.strip()
    if not stripped:
        return EndpointSummary(False, "", False, False)
    if allow_placeholders and has_placeholder(stripped):
        return EndpointSummary(True, "placeholder", True, True)
    parsed = urlparse(stripped)
    hostname = (parsed.hostname or "").lower()
    return EndpointSummary(True, parsed.scheme, bool(hostname), _is_private_or_internal_host(hostname))


def _is_private_or_internal_host(hostname: str) -> bool:
    if not hostname:
        return False
    if hostname in {"localhost", "127.0.0.1", "::1", "gigachat", "litellm"}:
        return True
    if hostname.endswith(".local") or hostname.endswith(".internal") or hostname.endswith(".lan"):
        return True
    try:
        address = ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def build_contract(values: dict[str, str], *, allow_placeholders: bool) -> dict[str, object]:
    deployment_mode = values.get("DEPLOYMENT_MODE", "offline_intranet").strip().lower()
    provider = values.get("LLM_PROVIDER", "gigachat").strip().lower()
    transport = values.get("LLM_TRANSPORT_MODE", "direct_gigachat").strip().lower() or "direct_gigachat"
    app_env = values.get("APP_ENV", "production").strip().lower()

    endpoints = {
        "gigachat_api": endpoint_summary(values.get("GIGACHAT_API_BASE_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
        "gigachat_auth": endpoint_summary(values.get("GIGACHAT_AUTH_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
        "litellm_gateway": endpoint_summary(values.get("LITELLM_GATEWAY_URL", ""), allow_placeholders=allow_placeholders).as_dict(),
    }

    errors: list[str] = []
    warnings: list[str] = []
    if deployment_mode == "offline_intranet" and provider != "gigachat":
        errors.append("offline_intranet requires LLM_PROVIDER=gigachat")
    if transport not in TRANSPORT_MODES:
        errors.append("LLM_TRANSPORT_MODE must be direct_gigachat or litellm_gateway")
    if transport == "direct_gigachat":
        if not values.get("GIGACHAT_API_BASE_URL", "").strip():
            errors.append("direct_gigachat requires GIGACHAT_API_BASE_URL")
        if not values.get("GIGACHAT_AUTH_URL", "").strip():
            errors.append("direct_gigachat requires GIGACHAT_AUTH_URL")
    if transport == "litellm_gateway" and not values.get("LITELLM_GATEWAY_URL", "").strip():
        errors.append("litellm_gateway requires LITELLM_GATEWAY_URL")
    if deployment_mode == "offline_intranet":
        for name, summary in endpoints.items():
            if summary["configured"] and not summary["private_or_internal"]:
                warnings.append(f"{name} endpoint does not look private/internal for offline_intranet")

    return {
        "status": "ready" if not errors else "not_ready",
        "deployment_mode": deployment_mode,
        "llm_provider": provider,
        "llm_transport_mode": transport,
        "default_provider": "gigachat",
        "server_roles": {
            "server_1": "KW Studio app, API, frontend, Postgres, artifact storage, workflows",
            "server_2": "Optional LiteLLM-compatible gateway and heavy CPU runtime modules",
            "server_3": "Local GigaChat runtime reachable only by internal ip:port",
        },
        "endpoints": endpoints,
        "environment": redacted_values(values),
        "optional_components": {
            "server_2_litellm_gateway": transport == "litellm_gateway" or bool(values.get("LITELLM_GATEWAY_URL", "").strip()),
            "server_2_heavy_runtime_modules": bool(values.get("LITELLM_GATEWAY_URL", "").strip()),
        },
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the KW Studio offline LLM topology contract without network calls.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--env-file", default=None, help="Env file to inspect. Defaults to .env.deploy, then .env.deploy.example.")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow CHANGE_ME placeholder endpoints for .env.deploy.example checks.")
    parser.add_argument("--json", action="store_true", help="Print only JSON output.")
    parser.add_argument("--require-ready", action="store_true", help="Fail if the topology contract has errors.")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Treat topology warnings as failures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2
    env_file = select_env_file(repo_root, args.env_file)
    values = merged_values(read_env_file(env_file))
    contract = build_contract(values, allow_placeholders=args.allow_placeholders)

    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print(f"[INFO] env_file={env_file if env_file is not None else '[none]'}")
        print("[llm-topology]")
        print(json.dumps(contract, indent=2, sort_keys=True))
        if contract["status"] == "ready":
            print("[PASS] LLM topology contract completed")
        else:
            print("[FAIL] LLM topology contract has errors")

    has_errors = bool(contract["errors"])
    has_warnings = bool(contract["warnings"])
    if args.require_ready and has_errors:
        return 1
    if args.warnings_as_errors and has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
