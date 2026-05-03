from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_runtime_phase_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_0_slides_runtime_phase_check_is_ready() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-runtime-phase-checkpoint"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.0"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf2_0"] is False
    assert payload["dependency_versions_changed_by_rf2_0"] is False
    assert payload["dockerfiles_changed_by_rf2_0"] is False
    assert payload["llm_topology_changed_by_rf2_0"] is False
    assert payload["browser_runtime_changed_by_rf2_0"] is False
    assert payload["default_llm_provider"] == "local_gigachat"
    assert payload["next_recommended_step"] == "RF2.1 — Slides runtime capability inventory and baseline smoke"
    assert payload["errors"] == []


def test_rf2_0_phase_plan_preserves_scope_and_non_goals() -> None:
    plan = (repo_root() / "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md").read_text(encoding="utf-8")

    assert "RF2.0 checkpoint" in plan
    assert "RF2.1 — Slides runtime capability inventory and baseline smoke" in plan
    assert "RF2.2 — Minimal deterministic PPTX generation from approved plan" in plan
    assert "RF2.6 — Slides provenance manifest emitted as downloadable artifact" in plan
    assert "Do not start RF2.1 until RF2.0 is accepted." in plan
    assert "npm audit fix --force" in plan
    assert "local GigaChat" in plan
    assert "does not change renderer behavior" in plan
    assert "does not change renderer behavior" in plan


def test_rf2_0_required_contract_surfaces_exist() -> None:
    root = repo_root()
    required = [
        "backend/app/services/slides_service/plan_first_contract.py",
        "scripts/kw_slides_plan_first_check.py",
        "scripts/kw_slides_task_events_check.py",
        "scripts/kw_slides_render_modes_check.py",
        "scripts/kw_slides_provenance_manifest_check.py",
        "scripts/kw_slides_plan_editor_check.py",
        "frontend/src/components/presentations/slides-plan-editor-panel.tsx",
        "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts",
        "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    ]

    missing = [path for path in required if not (root / path).exists()]
    assert missing == []


def test_rf2_0_production_readiness_gate_mentions_checkpoint() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides runtime phase checkpoint" in gate
    assert "scripts/kw_slides_runtime_phase_check.py" in gate
    assert "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md" in gate
    assert "backend/tests/smoke/test_rf2_0_slides_runtime_phase.py" in gate
