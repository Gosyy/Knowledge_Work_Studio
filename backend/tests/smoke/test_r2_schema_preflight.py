from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PREFLIGHT = REPO_ROOT / "scripts" / "kw_schema_preflight.py"
PRODUCTION_GATE = REPO_ROOT / "scripts" / "kw_production_readiness_gate.py"


def run_schema_preflight(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCHEMA_PREFLIGHT), "--repo-root", str(REPO_ROOT), *args]
    clean_env = os.environ.copy()
    clean_env.pop("DATABASE_URL", None)
    clean_env.pop("METADATA_BACKEND", None)
    if env:
        clean_env.update(env)
    return subprocess.run(command, cwd=REPO_ROOT, env=clean_env, text=True, capture_output=True, check=False)


def load_schema_module():
    spec = importlib.util.spec_from_file_location("kw_schema_preflight", SCHEMA_PREFLIGHT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r2_schema_preflight_explain_static_mode() -> None:
    result = run_schema_preflight("--explain")

    assert result.returncode == 0
    assert "[PASS] static Postgres schema manifest" in result.stdout
    assert "[schema-manifest]" in result.stdout
    assert "presentation_plan_snapshots" in result.stdout
    assert "schema preflight completed in static mode" in result.stdout


def test_r2_schema_preflight_require_ready_requires_database_url() -> None:
    result = run_schema_preflight("--require-ready")

    assert result.returncode == 2
    assert "DATABASE_URL is not configured" in result.stdout
    assert "password" not in result.stdout.lower()


def test_r2_schema_preflight_redacts_database_url_password() -> None:
    secret_password = "ultra_hidden_password_for_r2"
    dsn = f"postgresql://kw_user:{secret_password}@10.0.0.30:5432/kwstudio"
    result = run_schema_preflight("--explain", env={"DATABASE_URL": dsn})

    assert result.returncode == 0
    assert secret_password not in result.stdout
    assert '"password_configured": true' in result.stdout
    assert "10.0.0.30" in result.stdout


def test_r2_schema_preflight_non_postgres_backend_skips_without_require_ready() -> None:
    result = run_schema_preflight("--explain", env={"METADATA_BACKEND": "sqlite"})

    assert result.returncode == 0
    assert "metadata_backend=sqlite" in result.stdout
    assert "live schema validation skipped" in result.stdout


def test_r2_schema_manifest_contains_core_tables_and_columns() -> None:
    module = load_schema_module()
    manifest = module.SCHEMA_MANIFEST

    assert "sessions" in manifest
    assert "tasks" in manifest
    assert "artifacts" in manifest
    assert "presentation_plan_snapshots" in manifest
    assert "owner_user_id" in manifest["sessions"]
    assert "result_json" in manifest["tasks"]
    assert "storage_key" in manifest["artifacts"]
    assert "snapshot_json" in manifest["presentation_plan_snapshots"]


def test_r2_production_readiness_gate_runs_schema_preflight() -> None:
    content = PRODUCTION_GATE.read_text(encoding="utf-8")

    assert "scripts/kw_schema_preflight.py" in content
    assert "Postgres schema lifecycle preflight" in content
