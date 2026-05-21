from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_p6_deployment_packaging_files_are_present() -> None:
    required = [
        "Dockerfile.backend",
        "docker-compose.deploy.yml",
        ".env.deploy.example",
        ".dockerignore",
        "frontend/Dockerfile",
        "frontend/.dockerignore",
        "docs/deployment-packaging.md",
        "scripts/kw_validate_deployment_package.py",
    ]

    for path in required:
        assert (REPO_ROOT / path).is_file(), path


def test_p6_backend_dockerfile_is_runtime_safe() -> None:
    content = _read("Dockerfile.backend")

    assert "FROM python:3.12-slim" in content
    assert "PIP_NO_CACHE_DIR=1" in content
    assert "USER kwstudio" in content
    assert "HEALTHCHECK" in content
    assert "backend.app.main:app" in content
    assert "COPY backend ./backend" in content
    assert "COPY skills ./skills" in content
    assert "COPY . ." not in content


def test_p6_frontend_dockerfile_uses_standalone_runtime() -> None:
    content = _read("frontend/Dockerfile")
    next_config = _read("frontend/next.config.mjs")

    assert "FROM node:20-alpine" in content
    assert "npm ci --no-audit --no-fund --progress=false" in content
    assert "npm run build" in content
    assert ".next/standalone" in content
    assert "USER nextjs" in content
    assert 'CMD ["node", "server.js"]' in content
    assert 'output: "standalone"' in next_config


def test_p6_compose_uses_required_envs_and_healthchecks() -> None:
    content = _read("docker-compose.deploy.yml")

    assert "postgres:" in content
    assert "backend:" in content
    assert "frontend:" in content
    assert "DATABASE_URL: ${DATABASE_URL:?" in content
    assert "SECRET_KEY: ${SECRET_KEY:?" in content
    assert "STORAGE_ROOT: ${STORAGE_ROOT:-/app/storage}" in content
    assert "UPLOADS_DIR: ${UPLOADS_DIR:-/app/storage/uploads}" in content
    assert "ARTIFACTS_DIR: ${ARTIFACTS_DIR:-/app/storage/artifacts}" in content
    assert "TEMP_DIR: ${TEMP_DIR:-/app/storage/temp}" in content
    assert "kw_storage:/app/storage" in content
    assert "DEPLOYMENT_MODE: ${DEPLOYMENT_MODE:-offline_intranet}" in content
    assert "DEPLOYMENT_MODE: docker" not in content
    assert "condition: service_healthy" in content
    assert "kw_storage:" in content
    assert "postgres_data:" in content
    assert "sk-proj-" not in content
    assert "OPENAI_API_KEY=" not in content


def test_p6_requirements_include_postgres_driver() -> None:
    assert "psycopg[binary]>=3.1,<4.0" in _read("requirements.txt")


def test_p6_validation_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/kw_validate_deployment_package.py", "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] deployment packaging files are present" in result.stdout


def test_p6_env_example_aligns_storage_volume_paths() -> None:
    env_example = _read(".env.deploy.example")

    assert "STORAGE_ROOT=/app/storage" in env_example
    assert "UPLOADS_DIR=/app/storage/uploads" in env_example
    assert "ARTIFACTS_DIR=/app/storage/artifacts" in env_example
    assert "TEMP_DIR=/app/storage/temp" in env_example
