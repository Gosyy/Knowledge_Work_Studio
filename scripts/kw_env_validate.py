#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_KEYS = (
    "DEPLOYMENT_MODE",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "DATABASE_URL",
    "SECRET_KEY",
    "METADATA_BACKEND",
    "STORAGE_BACKEND",
    "STORAGE_ROOT",
    "UPLOADS_DIR",
    "ARTIFACTS_DIR",
    "TEMP_DIR",
    "LLM_PROVIDER",
    "GIGACHAT_API_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
)

SENSITIVE_KEY_PARTS = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "ACCESS_KEY",
    "DATABASE_URL",
    "AUTH_URL",
    "API_KEY",
)

PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "CHANGEME",
    "REPLACE_ME",
    "TODO",
    "YOUR_",
)

LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
LOW_ENTROPY_SECRET_MARKERS = (
    "secret",
    "password",
    "changeme",
    "change_me",
    "please_change",
    "minimum_32_char_secret_key",
)


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    key: str
    message: str


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def _strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    result: list[str] = []
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == "#" and not in_single and not in_double:
            if index == 0 or line[index - 1].isspace():
                break
        result.append(char)
    return "".join(result).strip()


def parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line.strip())
        if not line:
            continue
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
            if not key or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                continue
            values[key] = value.strip().strip('"').strip("'")
    return values


def parse_env_file(path: Path) -> dict[str, str]:
    return parse_env_text(path.read_text(encoding="utf-8"))


def is_sensitive_key(key: str) -> bool:
    upper_key = key.upper()
    return any(part in upper_key for part in SENSITIVE_KEY_PARTS)


def redact_value(key: str, value: str) -> str:
    if is_sensitive_key(key):
        return "[set]" if value.strip() else "[unset]"
    return value if value.strip() else "[unset]"


def redacted_summary(values: dict[str, str]) -> dict[str, str]:
    return {key: redact_value(key, values.get(key, "")) for key in REQUIRED_KEYS}


def has_placeholder(value: str) -> bool:
    upper_value = value.upper()
    return any(marker in upper_value for marker in PLACEHOLDER_MARKERS)


def secret_key_is_strong_enough(value: str, *, allow_placeholders: bool) -> bool:
    stripped = value.strip()
    if allow_placeholders and has_placeholder(stripped):
        return True
    if len(stripped) < 32:
        return False
    lowered = stripped.lower()
    if any(marker in lowered for marker in LOW_ENTROPY_SECRET_MARKERS):
        return False
    character_classes = sum(
        bool(pattern.search(stripped))
        for pattern in (re.compile(r"[a-z]"), re.compile(r"[A-Z]"), re.compile(r"[0-9]"), re.compile(r"[^A-Za-z0-9]"))
    )
    if character_classes < 3:
        return False
    if len(set(stripped)) < 12:
        return False
    return True


def classify_database_url(database_url: str) -> tuple[str, str | None]:
    if not database_url.strip():
        return "missing", None
    parsed = urlparse(database_url)
    scheme = parsed.scheme or "unknown"
    host = parsed.hostname
    if not scheme.startswith(("postgres", "postgresql")):
        return f"unsupported-scheme:{scheme}", host
    if host is None:
        return "postgres-host-missing", host
    if host in LOCAL_DB_HOSTS:
        return "postgres-localhost", host
    if host in {"postgres", "db", "database"} or host.endswith(".local") or host.endswith(".internal"):
        return "postgres-internal", host
    return "postgres-remote", host


def validate_environment(
    values: dict[str, str],
    *,
    allow_placeholders: bool,
    allow_localhost_db: bool,
    require_offline_profile: bool,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for key in REQUIRED_KEYS:
        value = values.get(key, "")
        if not value.strip():
            issues.append(ValidationIssue("error", key, "required value is empty or missing"))
        elif has_placeholder(value) and not allow_placeholders:
            issues.append(ValidationIssue("error", key, "placeholder value must be replaced"))

    secret_key = values.get("SECRET_KEY", "")
    if secret_key and not secret_key_is_strong_enough(secret_key, allow_placeholders=allow_placeholders):
        issues.append(
            ValidationIssue(
                "error",
                "SECRET_KEY",
                "SECRET_KEY must be at least 32 chars, non-placeholder, and contain diverse character classes",
            )
        )

    deployment_mode = values.get("DEPLOYMENT_MODE", "")
    app_env = values.get("APP_ENV", "")
    metadata_backend = values.get("METADATA_BACKEND", "")
    database_url = values.get("DATABASE_URL", "")
    db_classification, db_host = classify_database_url(database_url)

    if metadata_backend == "postgres" and not database_url.strip():
        issues.append(ValidationIssue("error", "DATABASE_URL", "METADATA_BACKEND=postgres requires DATABASE_URL"))
    if db_classification.startswith("unsupported-scheme") or db_classification == "postgres-host-missing":
        issues.append(ValidationIssue("error", "DATABASE_URL", f"DATABASE_URL classification is {db_classification}"))
    if app_env == "production" and db_classification == "postgres-localhost" and not allow_localhost_db:
        issues.append(
            ValidationIssue(
                "error",
                "DATABASE_URL",
                "localhost database is unsafe for production unless --allow-localhost-db is set",
            )
        )

    if db_host and db_host in LOCAL_DB_HOSTS and values.get("POSTGRES_HOST") not in {"", None, db_host}:
        issues.append(ValidationIssue("warning", "DATABASE_URL", "DATABASE_URL host differs from POSTGRES_HOST"))

    if require_offline_profile or deployment_mode == "offline_intranet":
        if values.get("LLM_PROVIDER") != "gigachat":
            issues.append(ValidationIssue("error", "LLM_PROVIDER", "offline_intranet deployment requires LLM_PROVIDER=gigachat"))
        for key in ("GIGACHAT_API_BASE_URL", "GIGACHAT_AUTH_URL"):
            value = values.get(key, "")
            if value and not (value.startswith("http://") or value.startswith("https://") or (allow_placeholders and has_placeholder(value))):
                issues.append(ValidationIssue("error", key, "GigaChat endpoint must be an internal http(s) URL"))

    if values.get("STORAGE_BACKEND") == "local":
        for key in ("STORAGE_ROOT", "UPLOADS_DIR", "ARTIFACTS_DIR", "TEMP_DIR"):
            value = values.get(key, "")
            if value and not value.startswith(("/", "./", "../")) and not (allow_placeholders and has_placeholder(value)):
                issues.append(ValidationIssue("warning", key, "local storage path should be explicit"))

    return issues


def choose_env_file(repo_root: Path, requested: str | None) -> tuple[Path, bool]:
    if requested:
        return Path(requested).expanduser().resolve(), False
    deployment_env = repo_root / ".env.deploy"
    if deployment_env.exists():
        return deployment_env, False
    return repo_root / ".env.deploy.example", True


def print_report(values: dict[str, str], issues: list[ValidationIssue], *, db_classification: str, db_host: str | None) -> None:
    print("[environment]")
    print(json.dumps(redacted_summary(values), indent=2, sort_keys=True))
    print("[database-url]")
    print(json.dumps({"classification": db_classification, "host_configured": bool(db_host)}, indent=2, sort_keys=True))
    if not issues:
        print("[PASS] environment validation completed")
        return
    print("[issues]")
    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.key}: {issue.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KW Studio deployment environment without printing secrets.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--env-file", default=None, help="Env file to validate. Defaults to .env.deploy, then .env.deploy.example.")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow CHANGE_ME placeholders, intended only for .env.deploy.example checks.")
    parser.add_argument("--allow-localhost-db", action="store_true", help="Allow localhost DATABASE_URL in APP_ENV=production.")
    parser.add_argument("--require-offline-profile", action="store_true", help="Require the approved offline intranet GigaChat profile.")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Treat validation warnings as errors.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    env_file, using_example = choose_env_file(repo_root, args.env_file)
    if not env_file.exists():
        print(f"[FAIL] env file does not exist: {env_file}")
        return 2

    values = parse_env_file(env_file)
    db_classification, db_host = classify_database_url(values.get("DATABASE_URL", ""))
    print(f"[INFO] repo_root={repo_root}")
    try:
        print(f"[INFO] env_file={env_file.resolve().relative_to(repo_root.resolve()).as_posix()}")
    except ValueError:
        print(f"[INFO] env_file={env_file}")
    if using_example and not args.allow_placeholders:
        print("[WARN] .env.deploy is absent; validating .env.deploy.example without --allow-placeholders will fail on CHANGE_ME markers")

    issues = validate_environment(
        values,
        allow_placeholders=args.allow_placeholders,
        allow_localhost_db=args.allow_localhost_db,
        require_offline_profile=args.require_offline_profile,
    )
    print_report(values, issues, db_classification=db_classification, db_host=db_host)

    has_errors = any(issue.severity == "error" for issue in issues)
    has_warnings = any(issue.severity == "warning" for issue in issues)
    if has_errors or (args.warnings_as_errors and has_warnings):
        print("[FAIL] environment validation failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
