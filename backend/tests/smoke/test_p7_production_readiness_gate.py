from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_p7_production_readiness_gate_files_are_present() -> None:
    required = [
        ".github/workflows/production-readiness.yml",
        "scripts/kw_production_readiness_gate.py",
        "backend/tests/smoke/test_p7_production_readiness_gate.py",
        "docs/production-readiness-final-gate.md",
    ]

    for path in required:
        assert (REPO_ROOT / path).is_file(), path


def test_p7_gate_script_checks_only_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/kw_production_readiness_gate.py", "--repo-root", str(REPO_ROOT), "--checks-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] required P-phase files are present" in result.stdout
    assert "[PASS] no forbidden secret markers found" in result.stdout


def test_p7_gate_script_references_all_major_final_checks() -> None:
    content = _read("scripts/kw_production_readiness_gate.py")

    assert "kw_validate_deployment_package.py" in content
    assert "kw_deployment_preflight.py" in content
    assert "kw_postgres_integration_gate.py" in content
    assert "pytest" in content
    assert "compileall" in content
    assert "npm" in content
    assert "test:e2e:smoke" in content
    assert "SECRET_MARKERS" in content
    assert "SECRET_MARKER_ALLOWLIST_FILES" in content


def test_p7_workflow_runs_final_gate_with_frontend_dependencies() -> None:
    workflow = _read(".github/workflows/production-readiness.yml")

    assert "Production readiness final gate" in workflow
    assert "actions/setup-python" in workflow
    assert "actions/setup-node" in workflow
    assert "npm ci --no-audit --no-fund --progress=false" in workflow
    assert "npx playwright install chromium" in workflow
    assert "scripts/kw_production_readiness_gate.py" in workflow
    assert "--postgres-mode safety" in workflow


def test_p7_makefile_target_exists() -> None:
    makefile = _read("Makefile")

    assert "production-readiness:" in makefile
    assert "scripts/kw_production_readiness_gate.py --repo-root ." in makefile
