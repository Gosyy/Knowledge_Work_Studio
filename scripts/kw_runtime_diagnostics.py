#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

SENSITIVE_KEY_PARTS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "ACCESS_KEY",
    "API_KEY",
    "CLIENT_SECRET",
    "DATABASE_URL",
)

ENV_KEYS = (
    "APP_ENV",
    "DEPLOYMENT_MODE",
    "METADATA_BACKEND",
    "STORAGE_BACKEND",
    "LLM_PROVIDER",
    "LLM_TRANSPORT_MODE",
    "DATABASE_URL",
    "SECRET_KEY",
    "POSTGRES_PASSWORD",
    "GIGACHAT_API_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
    "LITELLM_GATEWAY_URL",
    "LITELLM_GATEWAY_MODEL",
    "LITELLM_GATEWAY_API_KEY",
    "STORAGE_ROOT",
    "UPLOADS_DIR",
    "ARTIFACTS_DIR",
    "TEMP_DIR",
)

REQUIRED_PATHS = (
    "backend/app/main.py",
    "backend/app/api/routes/health.py",
    "backend/app/deployment.py",
    "backend/app/observability.py",
    "backend/app/core/config.py",
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    "scripts/kw_env_validate.py",
    "scripts/kw_schema_preflight.py",
    "scripts/kw_operator_backup.py",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


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


def is_sensitive_key(key: str) -> bool:
    normalized = key.upper()
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact_value(key: str, value: str | None) -> str:
    if is_sensitive_key(key):
        return "[set]" if value and value.strip() else "[unset]"
    return value or ""


def safe_environment(values: dict[str, str]) -> dict[str, str]:
    return {key: redact_value(key, values.get(key)) for key in ENV_KEYS if key in values or os.getenv(key) is not None}


def merged_environment(env_file_values: dict[str, str]) -> dict[str, str]:
    merged = dict(env_file_values)
    for key in ENV_KEYS:
        if os.getenv(key) is not None:
            merged[key] = os.getenv(key, "")
    return merged


def classify_database_url(database_url: str | None) -> dict[str, object]:
    value = (database_url or "").strip()
    if not value:
        return {"configured": False, "classification": "missing", "host_configured": False}

    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"postgresql", "postgresql+psycopg"}:
        return {"configured": True, "classification": "unsupported-scheme", "host_configured": bool(parsed.hostname)}

    hostname = (parsed.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        classification = "postgres-localhost"
    elif hostname in {"postgres", "db"} or hostname.endswith(".local") or hostname.endswith(".internal"):
        classification = "postgres-internal"
    elif hostname:
        classification = "postgres-remote"
    else:
        classification = "postgres-missing-host"

    return {"configured": True, "classification": classification, "host_configured": bool(hostname)}


def path_presence(repo_root: Path) -> dict[str, bool]:
    return {relative: (repo_root / relative).exists() for relative in REQUIRED_PATHS}


def build_diagnostics(repo_root: Path, env_file: Path | None) -> dict[str, object]:
    env_file_values = parse_env_file(env_file)
    env_values = merged_environment(env_file_values)
    paths = path_presence(repo_root)
    database = classify_database_url(env_values.get("DATABASE_URL"))
    diagnostics = {
        "repo_root": str(repo_root),
        "env_file": str(env_file) if env_file is not None else None,
        "deployment": {
            "app_env": env_values.get("APP_ENV", ""),
            "deployment_mode": env_values.get("DEPLOYMENT_MODE", ""),
            "metadata_backend": env_values.get("METADATA_BACKEND", ""),
            "storage_backend": env_values.get("STORAGE_BACKEND", ""),
            "llm_provider": env_values.get("LLM_PROVIDER", ""),
            "database_url": database,
        },
        "required_paths": paths,
        "environment": safe_environment(env_values),
    }
    missing_paths = [relative for relative, exists in paths.items() if not exists]
    diagnostics["status"] = "ok" if not missing_paths else "warning"
    diagnostics["warnings"] = [f"missing required path: {relative}" for relative in missing_paths]
    return diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print safe KW Studio runtime diagnostics without exposing secrets.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--env-file", default=None, help="Optional env file. Defaults to .env.deploy, then .env.deploy.example.")
    parser.add_argument("--json", action="store_true", help="Print only JSON diagnostics.")
    parser.add_argument("--require-paths", action="store_true", help="Fail when required deployment/runtime paths are missing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    env_file = select_env_file(repo_root, args.env_file)
    diagnostics = build_diagnostics(repo_root, env_file)

    if args.json:
        print(json.dumps(diagnostics, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print(f"[INFO] env_file={env_file if env_file is not None else '[none]'}")
        print("[diagnostics]")
        print(json.dumps(diagnostics, indent=2, sort_keys=True))
        if diagnostics["status"] == "ok":
            print("[PASS] runtime diagnostics completed")
        else:
            print("[WARN] runtime diagnostics completed with warnings")

    if args.require_paths and diagnostics["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
