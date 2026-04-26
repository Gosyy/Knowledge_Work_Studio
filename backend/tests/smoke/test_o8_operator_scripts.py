from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_o8_deployment_preflight_help() -> None:
    result = _run_script("scripts/kw_deployment_preflight.py", "--help")

    assert result.returncode == 0
    assert "deployment preflight" in result.stdout.lower()
    assert "--strict-ready" in result.stdout


def test_o8_operator_smoke_help() -> None:
    result = _run_script("scripts/kw_operator_smoke.py", "--help")

    assert result.returncode == 0
    assert "operator smoke" in result.stdout.lower()
    assert "--base-url" in result.stdout


def test_o8_deployment_preflight_lightweight_contract() -> None:
    result = _run_script(
        "scripts/kw_deployment_preflight.py",
        "--repo-root",
        str(REPO_ROOT),
        "--skip-readiness",
        "--skip-tests",
        "--skip-frontend",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] required deployment paths are present" in result.stdout
    assert "[PASS] deployment preflight completed" in result.stdout
    assert "SECRET_KEY_configured" in result.stdout
    assert "change-me" not in result.stdout
