from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.render_mode_contract import (
    ADAPTIVE_RENDER_MODE,
    TEMPLATE_RENDER_MODE,
    SLIDES_RENDER_MODE_CONTRACT,
    slides_render_mode_report,
    validate_render_request,
    validate_slides_render_mode_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_s6_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_render_modes_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_s6_render_mode_contract_is_ready() -> None:
    assert validate_slides_render_mode_contract() == []
    assert SLIDES_RENDER_MODE_CONTRACT.default_mode == ADAPTIVE_RENDER_MODE
    assert SLIDES_RENDER_MODE_CONTRACT.offline_ready is True
    assert SLIDES_RENDER_MODE_CONTRACT.provenance_required is True
    assert SLIDES_RENDER_MODE_CONTRACT.browser_policy == "none"


def test_s6_adaptive_mode_does_not_require_template_id() -> None:
    report = slides_render_mode_report(mode=ADAPTIVE_RENDER_MODE, plan_snapshot_id="plansnap_s6")
    assert report["status"] == "ready"
    assert report["policy"]["template_id_required"] is False
    assert report["policy"]["allows_adaptive_layout_selection"] is True


def test_s6_template_mode_requires_explicit_local_template_id() -> None:
    errors = validate_render_request(
        mode=TEMPLATE_RENDER_MODE,
        plan_snapshot_id="plansnap_s6",
        approved_plan=True,
        template_id=None,
    )
    assert "template_id is required for template render mode" in errors

    report = slides_render_mode_report(
        mode=TEMPLATE_RENDER_MODE,
        template_id="board_review_local",
        plan_snapshot_id="plansnap_s6",
    )
    assert report["status"] == "ready"
    assert report["policy"]["template_locked"] is True
    assert report["policy"]["allows_external_template_download"] is False


def test_s6_render_request_requires_approved_plan_and_snapshot() -> None:
    errors = validate_render_request(
        mode=ADAPTIVE_RENDER_MODE,
        plan_snapshot_id="",
        approved_plan=False,
    )
    assert "approved plan is required before rendering" in errors
    assert "plan_snapshot_id is required before rendering" in errors


def test_s6_cli_outputs_json_for_adaptive_mode() -> None:
    result = run_s6_check("--mode", "adaptive", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "adaptive"


def test_s6_cli_outputs_json_for_template_mode_with_template_id() -> None:
    result = run_s6_check(
        "--mode",
        "template",
        "--template-id",
        "board_review_local",
        "--json",
        "--require-ready",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "template"
    assert payload["request"]["template_id_configured"] is True


def test_s6_cli_rejects_template_mode_without_template_id_when_ready_required() -> None:
    result = run_s6_check("--mode", "template", "--require-ready")
    assert result.returncode != 0
    assert "template_id is required for template render mode" in result.stdout


def test_s6_cli_rejects_unknown_mode() -> None:
    result = run_s6_check("--mode", "classic", "--require-ready")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr
