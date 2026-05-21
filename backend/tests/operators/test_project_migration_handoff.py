from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_project_migration_handoff_cli_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_project_migration_handoff_check.py",
            "--repo-root",
            str(REPO_ROOT),
            "--json",
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["handoff_path"] == "docs/refactor/PROJECT_MIGRATION_HANDOFF.md"
    assert payload["missing_required_phrases"] == []


def test_project_migration_handoff_requires_future_patch_updates() -> None:
    text = (REPO_ROOT / "docs/refactor/PROJECT_MIGRATION_HANDOFF.md").read_text(encoding="utf-8")

    assert "Every future patch must review and update this file" in text
    assert "especially after the user and assistant agree on a new phase plan" in text
    assert "After every agreed new phase plan, update docs/refactor/PROJECT_MIGRATION_HANDOFF.md" in text
    assert "phase: KR-5A" in text


def test_production_gate_includes_project_migration_handoff_guardrail() -> None:
    gate_text = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Project migration handoff guardrail" in gate_text
    assert "scripts/kw_project_migration_handoff_check.py" in gate_text
