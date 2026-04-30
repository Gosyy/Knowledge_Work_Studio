import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_runtime_diagnostics.py"


def python_executable() -> str:
    return os.environ.get("KW_TEST_PYTHON", sys.executable)


def run_diagnostics(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [python_executable(), str(SCRIPT), "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r7_runtime_diagnostics_help() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "runtime diagnostics" in result.stdout.lower()


def test_r7_runtime_diagnostics_redacts_secrets_and_reports_core_backends(tmp_path: Path) -> None:
    secret = "super-secret-r7-value"
    env_file = tmp_path / ".env.deploy"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DEPLOYMENT_MODE=offline_intranet",
                "METADATA_BACKEND=postgres",
                "STORAGE_BACKEND=local",
                "LLM_PROVIDER=gigachat",
                f"DATABASE_URL=postgresql://kwstudio:{secret}@postgres:5432/kwstudio",
                f"SECRET_KEY={secret}",
                f"POSTGRES_PASSWORD={secret}",
                f"GIGACHAT_CLIENT_SECRET={secret}",
                "GIGACHAT_API_BASE_URL=http://gigachat.internal.local/api",
                "GIGACHAT_AUTH_URL=http://gigachat.internal.local/auth",
                "GIGACHAT_CLIENT_ID=kw_studio",
                "STORAGE_ROOT=/app/storage",
            ]
        ),
        encoding="utf-8",
    )

    result = run_diagnostics("--env-file", str(env_file))

    assert result.returncode == 0
    assert secret not in result.stdout
    assert '"deployment_mode": "offline_intranet"' in result.stdout
    assert '"metadata_backend": "postgres"' in result.stdout
    assert '"storage_backend": "local"' in result.stdout
    assert '"llm_provider": "gigachat"' in result.stdout
    assert '"classification": "postgres-internal"' in result.stdout
    assert "required_paths" in result.stdout


def test_r7_runtime_diagnostics_json_mode_is_parseable(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.deploy"
    env_file.write_text(
        "\n".join(
            [
                "DEPLOYMENT_MODE=offline_intranet",
                "METADATA_BACKEND=postgres",
                "STORAGE_BACKEND=local",
                "LLM_PROVIDER=gigachat",
                "DATABASE_URL=postgresql://kwstudio:secret@postgres:5432/kwstudio",
            ]
        ),
        encoding="utf-8",
    )

    result = run_diagnostics("--env-file", str(env_file), "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["deployment"]["metadata_backend"] == "postgres"
    assert payload["deployment"]["storage_backend"] == "local"
    assert payload["deployment"]["database_url"]["classification"] == "postgres-internal"
    assert payload["environment"]["DATABASE_URL"] == "[set]"
