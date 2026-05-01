from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.plan_first_contract import (
    SAFE_TASK_EVENTS,
    SLIDES_PLAN_FIRST_UX_CONTRACT,
    slides_plan_first_report,
    validate_slides_plan_first_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON = os.environ.get("KW_TEST_PYTHON", sys.executable)


def run_s3_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/kw_slides_plan_first_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_s3_plan_first_contract_is_ready() -> None:
    assert validate_slides_plan_first_contract() == []
    report = slides_plan_first_report()
    assert report["status"] == "ready"
    assert report["controls"]["direct_generate_without_plan_allowed"] is False


def test_s3_stage_order_requires_editable_plan_before_generation() -> None:
    stages = SLIDES_PLAN_FIRST_UX_CONTRACT.stages
    assert stages.index("outline_draft") < stages.index("editable_plan_review")
    assert stages.index("editable_plan_review") < stages.index("render_mode_selection")
    assert stages.index("render_mode_selection") < stages.index("approved_plan_generation")
    assert stages.index("approved_plan_generation") < stages.index("artifact_history_registration")


def test_s3_contract_requires_adaptive_and_template_modes() -> None:
    report = slides_plan_first_report()
    modes = set(report["contract"]["render_modes"])
    assert modes == {"adaptive", "template"}
    assert "adaptive_or_template_render_mode" in report["contract"]["kimi_derived_patterns"]


def test_s3_retry_from_saved_plan_and_safe_events_are_required() -> None:
    assert "slides.retry.from_saved_plan.requested" in SAFE_TASK_EVENTS
    assert "plan.snapshot.registered" in SAFE_TASK_EVENTS
    assert "artifact.registered" in SAFE_TASK_EVENTS
    assert SLIDES_PLAN_FIRST_UX_CONTRACT.retry_from_saved_plan_required is True


def test_s3_cli_outputs_json_for_template_mode() -> None:
    result = run_s3_check("--mode", "template", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "template"
    assert payload["controls"]["template_required"] is True


def test_s3_cli_outputs_json_for_adaptive_mode() -> None:
    result = run_s3_check("--mode", "adaptive", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "adaptive"
    assert payload["controls"]["template_required"] is False


def test_s3_cli_rejects_unknown_mode() -> None:
    result = run_s3_check("--mode", "classic", "--require-ready")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_s3_production_gate_includes_plan_first_step() -> None:
    gate_text = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "scripts/kw_slides_plan_first_check.py" in gate_text
    assert "Slides plan-first UX contract" in gate_text
    assert "docs/slides-plan-first-ux.md" in gate_text
