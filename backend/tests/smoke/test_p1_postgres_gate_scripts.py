from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = "scripts/kw_postgres_integration_gate.py"


def _run_script(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.pop("KW_POSTGRES_TEST_DATABASE_URL", None)
    merged_env.pop("POSTGRES_TEST_DATABASE_URL", None)
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, SCRIPT, "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def test_p1_postgres_gate_help() -> None:
    result = _run_script("--help")

    assert result.returncode == 0
    assert "postgres integration gate" in result.stdout.lower()
    assert "--require-dsn" in result.stdout
    assert "--safety-only" in result.stdout


def test_p1_postgres_gate_skips_without_dsn_by_default() -> None:
    result = _run_script("--safety-only")

    assert result.returncode == 0
    assert "[SKIP] no Postgres test DSN configured" in result.stdout
    assert "postgresql://" not in result.stdout


def test_p1_postgres_gate_requires_dsn_when_requested() -> None:
    result = _run_script("--require-dsn", "--safety-only")

    assert result.returncode == 2
    assert "[SKIP] no Postgres test DSN configured" in result.stdout
    assert "postgresql://" not in result.stdout


def test_p1_postgres_gate_rejects_production_like_database_without_printing_password() -> None:
    result = _run_script(
        "--safety-only",
        env={"KW_POSTGRES_TEST_DATABASE_URL": "postgresql://user:supersecret@localhost:5432/production"},
    )

    assert result.returncode == 2
    assert "production-like" in result.stdout
    assert "supersecret" not in result.stdout
    assert "postgresql://user" not in result.stdout


def test_p1_postgres_gate_accepts_safe_test_database_name_before_dependency_check() -> None:
    result = _run_script(
        "--safety-only",
        env={"KW_POSTGRES_TEST_DATABASE_URL": "postgresql://user:supersecret@localhost:5432/kwstudio_test"},
    )

    if result.returncode == 0:
        assert "[PASS] safety-only Postgres gate completed" in result.stdout
    else:
        assert result.returncode == 2
        assert "psycopg is not installed" in result.stdout
    assert '"database": "kwstudio_test"' in result.stdout
    assert '"password_configured": true' in result.stdout
    assert "supersecret" not in result.stdout
