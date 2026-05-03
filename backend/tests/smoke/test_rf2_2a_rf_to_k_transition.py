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
        [sys.executable, "scripts/kw_rf_to_k_transition_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_2a_transition_checker_reports_ready_without_runtime_changes() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "rf-to-k-transition-guard"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.2a"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf2_2a"] is False
    assert payload["dependency_versions_changed_by_rf2_2a"] is False
    assert payload["dockerfiles_changed_by_rf2_2a"] is False
    assert payload["frontend_runtime_changed_by_rf2_2a"] is False
    assert payload["llm_topology_changed_by_rf2_2a"] is False
    assert payload["browser_runtime_changed_by_rf2_2a"] is False


def test_rf2_2a_default_route_is_strict_rf_then_k() -> None:
    payload = json.loads(run_check("--json").stdout)

    assert payload["rf_must_finish_before_k_phase"] is True
    assert payload["rf_must_not_absorb_open_ended_k_phase_work"] is True
    assert payload["new_chat_prompt_must_include_plan"] is True
    assert payload["kimi_level_supported_now"] is False
    assert payload["k_phase_target"] == "whole_slides_product_loop_not_generator_only"
    assert payload["accepted_sequence_from_current_state"] == [
        "RF2.2a",
        "RF2.3",
        "RF2.4",
        "RF2.5",
        "RF2.6",
        "RF2.7",
        "RF2_closure",
        "RF3",
        "RF4",
        "RF_closure",
        "K0",
    ]


def test_rf2_2a_k_phase_plan_defines_whole_product_loop() -> None:
    content = (repo_root() / "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md").read_text(encoding="utf-8")

    assert "Kimi-level does not mean a single stronger PPTX generator" in content
    assert "source intake -> document understanding -> local/offline GigaChat planning" in content
    assert "K0 — Kimi-level rubric and golden deck benchmark" in content
    assert "K6 — End-to-end Kimi-like workflow" in content
    assert "direct local GigaChat-first" in content
    assert "Do not run `npm audit fix --force`" in content


def test_rf2_2a_rf_exit_criteria_keeps_rf_and_k_separate() -> None:
    content = (repo_root() / "docs/codex/RF_EXIT_TO_K_PHASE_CRITERIA.md").read_text(encoding="utf-8")

    assert "The project must finish RF before entering K-phase product-power work" in content
    assert "RF is not expected to reach Kimi-level slides quality" in content
    assert "RF must not absorb K-phase" in content
    assert "RF2.3 plan snapshot persistence and task event stream runtime wiring" in content
    assert "RF3 — Real document ingestion foundation" in content
    assert "RF4 — Local GigaChat integration hardening" in content
    assert "K-readiness matrix" in content


def test_rf2_2a_existing_phase_plans_link_to_transition_docs() -> None:
    runtime_plan = (repo_root() / "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md").read_text(encoding="utf-8")
    slides_plan = (repo_root() / "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md").read_text(encoding="utf-8")
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap" in runtime_plan
    assert "K_PHASE_PRODUCT_POWER_PLAN.md" in runtime_plan
    assert "RF_EXIT_TO_K_PHASE_CRITERIA.md" in runtime_plan
    assert "RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap" in slides_plan
    assert "RF2.3 remains the next runtime implementation step" in slides_plan
    assert "RF-to-K transition guard" in gate
    assert "scripts/kw_rf_to_k_transition_check.py" in gate
