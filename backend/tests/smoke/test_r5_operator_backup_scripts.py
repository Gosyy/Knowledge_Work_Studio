from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "kw_operator_backup.py"
RESTORE_CHECK_SCRIPT = REPO_ROOT / "scripts" / "kw_operator_restore_check.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r5_backup_dry_run_redacts_secrets_and_generates_backup_hints(tmp_path: Path) -> None:
    secret_password = "r5_super_hidden_password"
    secret_client = "r5_hidden_gigachat_secret"
    env_file = tmp_path / ".env.deploy"
    env_file.write_text(
        "\n".join(
            [
                "DEPLOYMENT_MODE=offline_intranet",
                "METADATA_BACKEND=postgres",
                "STORAGE_BACKEND=local",
                "POSTGRES_USER=kwstudio",
                f"POSTGRES_PASSWORD={secret_password}",
                "POSTGRES_DB=kwstudio",
                "DATABASE_URL=postgresql://kwstudio:r5_url_secret@postgres:5432/kwstudio",
                "STORAGE_ROOT=/app/storage",
                "LLM_PROVIDER=gigachat",
                "GIGACHAT_CLIENT_ID=kw_studio",
                f"GIGACHAT_CLIENT_SECRET={secret_client}",
            ]
        ),
        encoding="utf-8",
    )

    result = run_script(
        BACKUP_SCRIPT,
        "--dry-run",
        "--env-file",
        str(env_file),
        "--timestamp",
        "20260430T120000Z",
    )

    assert result.returncode == 0
    assert "operator backup dry-run plan generated" in result.stdout
    assert "pg_dump" in result.stdout
    assert "kw_storage" in result.stdout
    assert "sha256sum" in result.stdout
    assert "[set]" in result.stdout
    assert secret_password not in result.stdout
    assert secret_client not in result.stdout
    assert "r5_url_secret" not in result.stdout


def test_r5_backup_refuses_non_dry_run_execution() -> None:
    result = run_script(BACKUP_SCRIPT)

    assert result.returncode == 2
    assert "dry-run only" in result.stdout.lower()


def test_r5_restore_check_dry_run_is_non_destructive() -> None:
    result = run_script(
        RESTORE_CHECK_SCRIPT,
        "--dry-run",
        "--backup-dir",
        "backups/20260430T120000Z",
    )

    assert result.returncode == 0
    assert "operator restore-check dry-run plan generated" in result.stdout
    assert "pg_restore --list" in result.stdout
    assert "tar -tzf" in result.stdout
    assert "no database writes" in result.stdout
    assert " pg_restore -d " not in result.stdout
    assert "docker compose exec" not in result.stdout


def test_r5_restore_check_require_files_validates_expected_backup_files(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "postgres.dump").write_text("placeholder dump", encoding="utf-8")
    (backup_dir / "kw_storage.tar.gz").write_text("placeholder archive", encoding="utf-8")

    present = run_script(RESTORE_CHECK_SCRIPT, "--dry-run", "--backup-dir", str(backup_dir), "--require-files")
    assert present.returncode == 0

    missing = run_script(RESTORE_CHECK_SCRIPT, "--dry-run", "--backup-dir", str(tmp_path / "missing"), "--require-files")
    assert missing.returncode == 2
    assert "missing backup file" in missing.stdout


def test_r5_backup_plan_uses_expected_compose_and_volume_names() -> None:
    module = load_module(BACKUP_SCRIPT, "kw_operator_backup")
    plan = module.build_backup_plan(
        repo_root=REPO_ROOT,
        env_file=REPO_ROOT / ".env.deploy.example",
        compose_file=REPO_ROOT / "docker-compose.deploy.yml",
        project_name="kw-studio-r5",
        backup_dir=REPO_ROOT / "backups" / "r5-test",
    )
    commands = "\n".join(command for _, command in plan)

    assert "docker compose" in commands
    assert "docker-compose.deploy.yml" in commands
    assert "kw-studio-r5_kw_storage:/data:ro" in commands
    assert "$POSTGRES_USER" in commands
    assert "$POSTGRES_DB" in commands


def test_r5_scripts_expose_help() -> None:
    backup = run_script(BACKUP_SCRIPT, "--help")
    restore = run_script(RESTORE_CHECK_SCRIPT, "--help")

    assert backup.returncode == 0
    assert restore.returncode == 0
    assert "--dry-run" in backup.stdout
    assert "--dry-run" in restore.stdout
