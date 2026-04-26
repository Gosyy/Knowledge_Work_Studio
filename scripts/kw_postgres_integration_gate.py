#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

POSTGRES_TEST_PATH = "backend/tests/integrations/test_o4_postgres_revision_plan_persistence.py"
DSN_ENV_KEYS = ("KW_POSTGRES_TEST_DATABASE_URL", "POSTGRES_TEST_DATABASE_URL")
FORBIDDEN_DATABASE_TOKENS = ("prod", "production", "live", "main", "master")
SAFE_DATABASE_TOKENS = ("test", "ci", "local", "dev")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def configured_dsn() -> tuple[str | None, str | None]:
    for key in DSN_ENV_KEYS:
        value = os.getenv(key, "").strip()
        if value:
            return key, value
    return None, None


def normalize_dsn(dsn: str) -> str:
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def parse_dsn(dsn: str):
    return urlparse(normalize_dsn(dsn))


def dsn_summary(dsn: str) -> dict[str, object]:
    parsed = parse_dsn(dsn)
    database_name = parsed.path.lstrip("/")
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": parsed.port,
        "database": database_name,
        "username_configured": bool(parsed.username),
        "password_configured": bool(parsed.password),
    }


def validate_postgres_test_dsn(dsn: str, *, allow_non_test_database_name: bool) -> tuple[bool, str]:
    parsed = parse_dsn(dsn)
    if parsed.scheme not in {"postgresql", "postgres"}:
        return False, "Postgres test DSN must use postgresql:// or postgres://."

    database_name = parsed.path.lstrip("/")
    if not database_name:
        return False, "Postgres test DSN must include a database name."

    lowered = database_name.lower()
    if lowered in {"postgres", "template0", "template1"}:
        return False, "Refusing to run integration tests against a default/system database."

    if any(token in lowered for token in FORBIDDEN_DATABASE_TOKENS):
        return False, "Refusing to run integration tests against a database name that looks production-like."

    if not allow_non_test_database_name and not any(token in lowered for token in SAFE_DATABASE_TOKENS):
        return (
            False,
            "Refusing to run integration tests because database name does not look like a test database. "
            "Use a database name containing test/ci/local/dev or pass --allow-non-test-database-name.",
        )

    return True, "Postgres test DSN passed safety checks."


def check_psycopg_available() -> tuple[bool, str]:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return False, "psycopg is not installed. Install psycopg[binary] for the real Postgres gate."
    return True, "psycopg is installed."


def run_postgres_tests(repo_root: Path, *, extra_pytest_args: list[str]) -> int:
    command = [sys.executable, "-m", "pytest", POSTGRES_TEST_PATH, "-q", *extra_pytest_args]
    print(f"[postgres-tests] $ {' '.join(command)}")
    completed = subprocess.run(command, cwd=repo_root, check=False)
    print(f"[postgres-tests] exit={completed.returncode}")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the real Postgres integration gate for KW Studio without printing database credentials.",
    )
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument(
        "--require-dsn",
        action="store_true",
        help="Fail instead of skipping when no Postgres test DSN is configured.",
    )
    parser.add_argument(
        "--allow-non-test-database-name",
        action="store_true",
        help="Allow a database name that does not contain test/ci/local/dev after other safety checks pass.",
    )
    parser.add_argument(
        "--safety-only",
        action="store_true",
        help="Validate environment and DSN safety but do not run pytest.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional arguments appended to the focused pytest invocation after --.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    print(f"[INFO] repo_root={repo_root}")
    print(f"[INFO] python={sys.executable}")

    if not (repo_root / POSTGRES_TEST_PATH).exists():
        print(f"[FAIL] missing Postgres integration test: {POSTGRES_TEST_PATH}")
        return 2

    dsn_key, dsn = configured_dsn()
    if not dsn:
        message = (
            "[SKIP] no Postgres test DSN configured. Set KW_POSTGRES_TEST_DATABASE_URL "
            "or POSTGRES_TEST_DATABASE_URL to run the real Postgres gate."
        )
        print(message)
        return 2 if args.require_dsn else 0

    print(f"[INFO] dsn_env={dsn_key}")
    print("[INFO] dsn_summary=" + json.dumps(dsn_summary(dsn), sort_keys=True))

    is_safe, safety_message = validate_postgres_test_dsn(
        dsn,
        allow_non_test_database_name=args.allow_non_test_database_name,
    )
    if not is_safe:
        print(f"[FAIL] {safety_message}")
        return 2
    print(f"[PASS] {safety_message}")

    psycopg_ok, psycopg_message = check_psycopg_available()
    if not psycopg_ok:
        print(f"[FAIL] {psycopg_message}")
        return 2
    print(f"[PASS] {psycopg_message}")

    if args.safety_only:
        print("[PASS] safety-only Postgres gate completed")
        return 0

    extra_args = args.pytest_args
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    return run_postgres_tests(repo_root, extra_pytest_args=extra_args)


if __name__ == "__main__":
    raise SystemExit(main())
