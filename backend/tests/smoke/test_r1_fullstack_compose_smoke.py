from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_fullstack_compose_smoke.py"


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("kw_fullstack_compose_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["kw_fullstack_compose_smoke"] = module
    spec.loader.exec_module(module)
    return module


def test_r1_fullstack_compose_smoke_files_are_present() -> None:
    required = [
        "scripts/kw_fullstack_compose_smoke.py",
        ".github/workflows/fullstack-compose-smoke.yml",
        "docs/fullstack-compose-smoke.md",
        "backend/tests/smoke/test_r1_fullstack_compose_smoke.py",
    ]

    for path in required:
        assert (REPO_ROOT / path).is_file(), path


def test_r1_check_only_does_not_require_docker_to_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "--repo-root", str(REPO_ROOT), "--check-only"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] deployment compose files are present" in result.stdout
    assert "[PASS] check-only full-stack compose smoke validation completed" in result.stdout
    assert "CHANGE_ME" not in result.stdout


def test_r1_script_contains_required_compose_lifecycle_steps() -> None:
    content = _read("scripts/kw_fullstack_compose_smoke.py")

    assert "docker compose" in content
    assert "--check-only" in content
    assert "build" in content
    assert "up" in content
    assert "down" in content
    assert "/health" in content
    assert "/ready" in content
    assert "kw_operator_smoke.py" in content
    assert "logs" in content
    assert "--keep-running" in content
    assert "redact_text" in content


def test_r1_generated_env_is_valid_and_redacted() -> None:
    module = _load_script()
    values = module.build_generated_env(backend_port=8017, frontend_port=3017)

    assert module.validate_deployment_env(values) == []
    assert values["DEPLOYMENT_MODE"] == "offline_intranet"
    assert values["LLM_PROVIDER"] == "gigachat"
    assert values["GIGACHAT_API_BASE_URL"]
    assert values["GIGACHAT_AUTH_URL"]
    assert values["GIGACHAT_CLIENT_ID"]
    assert values["GIGACHAT_CLIENT_SECRET"]
    assert values["STORAGE_ROOT"] == "/app/storage"
    assert values["UPLOADS_DIR"] == "/app/storage/uploads"
    assert values["ARTIFACTS_DIR"] == "/app/storage/artifacts"
    assert values["TEMP_DIR"] == "/app/storage/temp"
    assert values["BACKEND_PORT"] == "8017"
    assert values["FRONTEND_PORT"] == "3017"
    assert "CHANGE_ME" not in "\n".join(values.values())

    redacted = module.redact_text(
        f"POSTGRES_PASSWORD={values['POSTGRES_PASSWORD']}\nDATABASE_URL={values['DATABASE_URL']}\nGIGACHAT_CLIENT_SECRET={values['GIGACHAT_CLIENT_SECRET']}",
        values,
    )
    assert values["POSTGRES_PASSWORD"] not in redacted
    assert values["DATABASE_URL"] not in redacted
    assert values["GIGACHAT_CLIENT_SECRET"] not in redacted
    assert "[REDACTED]" in redacted


def test_r1_docker_availability_is_warning_only_in_check_only(monkeypatch) -> None:
    module = _load_script()
    monkeypatch.setattr(module.shutil, "which", lambda name: None)

    check_only = module.check_docker_availability(check_only=True)
    real_run = module.check_docker_availability(check_only=False)

    assert check_only.errors == ()
    assert check_only.warnings
    assert real_run.errors


def test_r1_workflow_is_manual_and_makefile_targets_exist() -> None:
    workflow = _read(".github/workflows/fullstack-compose-smoke.yml")
    makefile = _read("Makefile")

    assert "workflow_dispatch" in workflow
    assert "kw_fullstack_compose_smoke.py --repo-root . --check-only" in workflow
    assert "kw_fullstack_compose_smoke.py --repo-root . --timeout" in workflow
    assert "fullstack-compose-smoke:" in makefile
    assert "fullstack-compose-smoke-check:" in makefile


def test_r1_backend_image_includes_runtime_skill_package() -> None:
    dockerfile = _read("Dockerfile.backend")

    assert "COPY backend ./backend" in dockerfile
    assert "COPY skills ./skills" in dockerfile
    assert "COPY . ." not in dockerfile


def test_r1_compose_uses_readiness_compatible_deployment_mode() -> None:
    compose = _read("docker-compose.deploy.yml")
    env_example = _read(".env.deploy.example")

    assert "DEPLOYMENT_MODE: ${DEPLOYMENT_MODE:-offline_intranet}" in compose
    assert "DEPLOYMENT_MODE: docker" not in compose
    assert "DEPLOYMENT_MODE=offline_intranet" in env_example
    assert "LLM_PROVIDER=gigachat" in env_example
    assert "GIGACHAT_CLIENT_SECRET=CHANGE_ME_GIGACHAT_CLIENT_SECRET" in env_example


def test_r1_compose_maps_local_storage_env_to_writable_backend_volume() -> None:
    compose = _read("docker-compose.deploy.yml")
    env_example = _read(".env.deploy.example")

    assert "kw_storage:/app/storage" in compose
    assert "STORAGE_ROOT: ${STORAGE_ROOT:-/app/storage}" in compose
    assert "UPLOADS_DIR: ${UPLOADS_DIR:-/app/storage/uploads}" in compose
    assert "ARTIFACTS_DIR: ${ARTIFACTS_DIR:-/app/storage/artifacts}" in compose
    assert "TEMP_DIR: ${TEMP_DIR:-/app/storage/temp}" in compose
    assert "STORAGE_ROOT=/app/storage" in env_example
