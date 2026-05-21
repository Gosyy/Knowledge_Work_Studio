#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

SCHEMA_MANIFEST: dict[str, tuple[str, ...]] = {
    "users": (
        "id",
        "email",
        "password_hash",
        "display_name",
        "is_active",
        "is_superuser",
        "created_at",
        "updated_at",
    ),
    "sessions": (
        "id",
        "owner_user_id",
        "created_at",
    ),
    "tasks": (
        "id",
        "session_id",
        "owner_user_id",
        "task_type",
        "status",
        "result_json",
        "error_message",
        "started_at",
        "completed_at",
        "created_at",
    ),
    "artifacts": (
        "id",
        "session_id",
        "task_id",
        "owner_user_id",
        "filename",
        "content_type",
        "storage_backend",
        "storage_key",
        "storage_uri",
        "size_bytes",
        "created_at",
    ),
    "uploaded_files": (
        "id",
        "session_id",
        "owner_user_id",
        "original_filename",
        "content_type",
        "size_bytes",
        "storage_backend",
        "storage_key",
        "storage_uri",
        "created_at",
    ),
    "stored_files": (
        "id",
        "session_id",
        "task_id",
        "kind",
        "file_type",
        "mime_type",
        "title",
        "original_filename",
        "storage_backend",
        "storage_key",
        "storage_uri",
        "checksum_sha256",
        "size_bytes",
        "is_remote",
        "owner_user_id",
        "created_at",
        "updated_at",
    ),
    "documents": (
        "id",
        "session_id",
        "current_file_id",
        "document_type",
        "title",
        "status",
        "created_at",
        "updated_at",
    ),
    "document_versions": (
        "id",
        "document_id",
        "file_id",
        "version_number",
        "created_from_task_id",
        "parent_version_id",
        "change_summary",
        "created_at",
    ),
    "presentations": (
        "id",
        "session_id",
        "current_file_id",
        "presentation_type",
        "title",
        "status",
        "created_at",
        "updated_at",
    ),
    "presentation_versions": (
        "id",
        "presentation_id",
        "file_id",
        "version_number",
        "created_from_task_id",
        "parent_version_id",
        "change_summary",
        "created_at",
    ),
    "presentation_plan_snapshots": (
        "id",
        "presentation_id",
        "presentation_version_id",
        "snapshot_json",
        "created_from_task_id",
        "change_summary",
        "created_at",
    ),
    "artifact_sources": (
        "id",
        "artifact_id",
        "source_file_id",
        "source_document_id",
        "source_presentation_id",
        "role",
        "created_at",
    ),
    "derived_contents": (
        "id",
        "file_id",
        "content_kind",
        "text_content",
        "structured_json",
        "outline_json",
        "language",
        "created_at",
        "updated_at",
    ),
}

POSTGRES_BACKENDS = {"postgres", "postgresql"}


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def load_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def first_configured(*values: str | None) -> str:
    for value in values:
        if value is not None and value.strip():
            return value.strip()
    return ""


def normalize_dsn(dsn: str) -> str:
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def dsn_summary(dsn: str) -> dict[str, object]:
    parsed = urlparse(normalize_dsn(dsn))
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": parsed.port,
        "database": parsed.path.lstrip("/"),
        "username_configured": bool(parsed.username),
        "password_configured": bool(parsed.password),
    }


def print_dsn_summary(database_url: str) -> None:
    if not database_url:
        print("[INFO] database_url_configured=false")
        return
    print("[INFO] database_url_summary=" + json.dumps(dsn_summary(database_url), sort_keys=True))


def manifest_summary() -> dict[str, object]:
    return {
        "table_count": len(SCHEMA_MANIFEST),
        "critical_column_count": sum(len(columns) for columns in SCHEMA_MANIFEST.values()),
        "tables": {table: list(columns) for table, columns in sorted(SCHEMA_MANIFEST.items())},
    }


def validate_static_manifest() -> list[str]:
    errors: list[str] = []
    if not SCHEMA_MANIFEST:
        errors.append("schema manifest is empty")
    for table_name, columns in sorted(SCHEMA_MANIFEST.items()):
        if not table_name:
            errors.append("schema manifest contains an empty table name")
        if not columns:
            errors.append(f"schema manifest table {table_name!r} has no critical columns")
        duplicates = sorted({column for column in columns if columns.count(column) > 1})
        for duplicate in duplicates:
            errors.append(f"schema manifest table {table_name!r} has duplicate column {duplicate!r}")
    return errors


def require_psycopg():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required for live schema validation") from exc
    return psycopg


def fetch_live_columns(database_url: str) -> dict[str, set[str]]:
    psycopg = require_psycopg()
    actual: dict[str, set[str]] = {}
    with psycopg.connect(normalize_dsn(database_url)) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
        )
        for table_name, column_name in cursor.fetchall():
            if table_name in SCHEMA_MANIFEST:
                actual.setdefault(str(table_name), set()).add(str(column_name))
    return actual


def evaluate_live_schema(actual: Mapping[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for table_name, expected_columns in sorted(SCHEMA_MANIFEST.items()):
        actual_columns = actual.get(table_name)
        if not actual_columns:
            errors.append(f"missing table: {table_name}")
            continue
        for column in expected_columns:
            if column not in actual_columns:
                errors.append(f"missing column: {table_name}.{column}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "KW Studio Postgres schema lifecycle preflight. "
            "Defaults to static manifest validation and never mutates schema."
        ),
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional env file to read. Defaults to .env.deploy when present; missing files are ignored.",
    )
    parser.add_argument("--metadata-backend", default="", help="Override metadata backend for this check.")
    parser.add_argument("--database-url", default="", help="Override DATABASE_URL for this check. Value is never printed.")
    parser.add_argument("--explain", action="store_true", help="Print the expected schema manifest.")
    parser.add_argument("--check-live", action="store_true", help="Validate a live Postgres database when DATABASE_URL is configured.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Require a live Postgres database and fail if schema is not ready.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    env_file = Path(args.env_file).expanduser().resolve() if args.env_file else repo_root / ".env.deploy"
    env_values = load_env_file(env_file)

    metadata_backend = first_configured(
        args.metadata_backend,
        os.getenv("METADATA_BACKEND"),
        env_values.get("METADATA_BACKEND"),
        "postgres",
    ).lower()

    database_url = first_configured(
        args.database_url,
        os.getenv("DATABASE_URL"),
        env_values.get("DATABASE_URL"),
    )

    print(f"[INFO] repo_root={repo_root}")
    print(f"[INFO] metadata_backend={metadata_backend}")
    print_dsn_summary(database_url)

    static_errors = validate_static_manifest()
    if static_errors:
        for error in static_errors:
            print(f"[FAIL] {error}")
        return 2

    summary = manifest_summary()
    print(
        "[PASS] static Postgres schema manifest includes "
        f"{summary['table_count']} table(s) and {summary['critical_column_count']} critical column(s)"
    )

    if args.explain:
        print("[schema-manifest]")
        print(json.dumps(summary, indent=2, sort_keys=True))

    if metadata_backend not in POSTGRES_BACKENDS:
        message = f"metadata_backend={metadata_backend!r} is not Postgres; live schema validation skipped"
        if args.require_ready:
            print(f"[FAIL] --require-ready requires Postgres metadata backend; {message}")
            return 2
        print(f"[SKIP] {message}")
        return 0

    if not database_url:
        if args.require_ready:
            print("[FAIL] --require-ready requested but DATABASE_URL is not configured")
            return 2
        if args.check_live:
            print("[SKIP] --check-live requested but DATABASE_URL is not configured")
            return 0
        print("[PASS] schema preflight completed in static mode")
        return 0

    if not args.check_live and not args.require_ready:
        print("[OK] DATABASE_URL is configured; live validation requires --check-live or --require-ready")
        print("[PASS] schema preflight completed in static mode")
        return 0

    try:
        actual_columns = fetch_live_columns(database_url)
    except Exception as exc:
        print(f"[FAIL] live schema validation could not read Postgres metadata: {exc.__class__.__name__}")
        return 2

    live_errors = evaluate_live_schema(actual_columns)
    if live_errors:
        for error in live_errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] live Postgres schema is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
