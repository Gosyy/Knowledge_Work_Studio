from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "kw_env_validate.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENV_VALIDATE_SCRIPT), "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_module():
    spec = importlib.util.spec_from_file_location("kw_env_validate", ENV_VALIDATE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["kw_env_validate"] = module
    spec.loader.exec_module(module)
    return module


def write_env(path: Path, *, secret: str = "KwStudioProdKey-2026-Offline!A1x", database_url: str = "postgresql://kwstudio:db_secret@postgres:5432/kwstudio") -> None:
    path.write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DEPLOYMENT_MODE=offline_intranet",
                "POSTGRES_USER=kwstudio",
                "POSTGRES_PASSWORD=db_secret",
                "POSTGRES_DB=kwstudio",
                f"DATABASE_URL={database_url}",
                f"SECRET_KEY={secret}",
                "METADATA_BACKEND=postgres",
                "STORAGE_BACKEND=local",
                "STORAGE_ROOT=/app/storage",
                "UPLOADS_DIR=/app/storage/uploads",
                "ARTIFACTS_DIR=/app/storage/artifacts",
                "TEMP_DIR=/app/storage/temp",
                "LLM_PROVIDER=gigachat",
                "GIGACHAT_API_BASE_URL=http://gigachat.local:9000/api",
                "GIGACHAT_AUTH_URL=http://gigachat.local:9000/auth",
                "GIGACHAT_CLIENT_ID=kw_studio",
                "GIGACHAT_CLIENT_SECRET=gigachat_secret",
            ]
        ),
        encoding="utf-8",
    )


def test_r6_example_env_allows_placeholders_and_redacts_values() -> None:
    result = run_script("--env-file", ".env.deploy.example", "--allow-placeholders")
    assert result.returncode == 0
    assert "environment validation completed" in result.stdout
    assert "[set]" in result.stdout
    assert "CHANGE_ME_POSTGRES_PASSWORD" not in result.stdout
    assert "CHANGE_ME_GIGACHAT_CLIENT_SECRET" not in result.stdout


def test_r6_placeholders_fail_without_allow_flag() -> None:
    result = run_script("--env-file", ".env.deploy.example")
    assert result.returncode == 1
    assert "placeholder value must be replaced" in result.stdout
    assert "CHANGE_ME_POSTGRES_PASSWORD" not in result.stdout


def test_r6_rejects_weak_secret_key(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.deploy"
    write_env(env_file, secret="too-short")
    result = run_script("--env-file", str(env_file))
    assert result.returncode == 1
    assert "SECRET_KEY" in result.stdout
    assert "too-short" not in result.stdout


def test_r6_rejects_localhost_database_in_production_unless_allowed(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.deploy"
    write_env(env_file, database_url="postgresql://kwstudio:db_secret@localhost:5432/kwstudio")
    blocked = run_script("--env-file", str(env_file))
    assert blocked.returncode == 1
    assert "localhost database is unsafe" in blocked.stdout
    assert "db_secret" not in blocked.stdout

    allowed = run_script("--env-file", str(env_file), "--allow-localhost-db")
    assert allowed.returncode == 0


def test_r6_missing_required_values_are_reported_without_printing_secret_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.deploy"
    write_env(env_file)
    text = env_file.read_text(encoding="utf-8").replace("GIGACHAT_CLIENT_SECRET=gigachat_secret", "GIGACHAT_CLIENT_SECRET=")
    env_file.write_text(text, encoding="utf-8")
    result = run_script("--env-file", str(env_file))
    assert result.returncode == 1
    assert "GIGACHAT_CLIENT_SECRET" in result.stdout
    assert "gigachat_secret" not in result.stdout
    assert "db_secret" not in result.stdout


def test_r6_parser_handles_minified_env_example_style() -> None:
    module = load_module()
    values = module.parse_env_text(
        "# comment before values\nAPP_ENV=production DEPLOYMENT_MODE=offline_intranet POSTGRES_USER=kwstudio\n"
        "DATABASE_URL=postgresql://kw:secret@postgres:5432/kw SECRET_KEY=KwStudioProdKey-2026-Offline!A1x"
    )
    assert values["APP_ENV"] == "production"
    assert values["DEPLOYMENT_MODE"] == "offline_intranet"
    assert values["DATABASE_URL"].startswith("postgresql://")
    assert values["SECRET_KEY"].startswith("KwStudioProdKey")


def test_r6_database_url_classification() -> None:
    module = load_module()
    assert module.classify_database_url("postgresql://u:p@postgres:5432/db")[0] == "postgres-internal"
    assert module.classify_database_url("postgresql://u:p@127.0.0.1:5432/db")[0] == "postgres-localhost"
    assert module.classify_database_url("sqlite:///tmp.db")[0].startswith("unsupported-scheme")


def test_r6_script_exposes_help() -> None:
    result = run_script("--help")
    assert result.returncode == 0
    assert "--allow-placeholders" in result.stdout
    assert "--allow-localhost-db" in result.stdout
