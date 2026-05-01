from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.workflows.visual_qa_planning_contract import (
    VISUAL_QA_REQUIRED_CHECKS,
    VISUAL_QA_REQUIRED_EVENTS,
    build_visual_qa_plan_manifest,
    build_visual_qa_report,
    validate_visual_qa_plan_manifest,
    visual_qa_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_s10_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_visual_qa_planning_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_s10_visual_qa_contract_is_planning_only_and_offline() -> None:
    contract = visual_qa_contract()
    assert contract["workflow_id"] == "visual_qa_planning"
    assert contract["offline_ready"] is True
    assert contract["runtime_scope"] == "contract_only_no_multimodal_runtime"
    assert contract["visual_runtime_required"] is False
    assert contract["external_model_allowed"] is False
    assert contract["internet_required"] is False
    assert contract["server_2_heavy_runtime_optional"] is True


def test_s10_slides_manifest_is_ready_and_links_artifact_references() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    assert validate_visual_qa_plan_manifest(manifest) == []
    assert manifest["mode"] == "slides"
    assert manifest["plan"]["source_artifacts"][0]["source_type"] == "pptx_artifact"
    assert manifest["plan"]["evidence_policy"]["store_artifact_references_only"] is True
    assert manifest["plan"]["evidence_policy"]["raw_pixels_allowed"] is False


def test_s10_artifact_manifest_is_ready_and_uses_no_external_runtime() -> None:
    report = build_visual_qa_report("artifact")
    assert report["status"] == "ready"
    assert report["manifest"]["mode"] == "artifact"
    assert report["manifest"]["visual_runtime_required"] is False
    assert report["manifest"]["external_model_allowed"] is False


def test_s10_manifest_includes_required_events_and_checks() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    event_refs = set(manifest["event_refs"])
    check_ids = {check["check_id"] for check in manifest["plan"]["checks"]}
    for event_name in VISUAL_QA_REQUIRED_EVENTS:
        assert event_name in event_refs
    for check_id in VISUAL_QA_REQUIRED_CHECKS:
        assert check_id in check_ids


def test_s10_validator_rejects_visual_runtime_requirement() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    manifest["visual_runtime_required"] = True
    errors = validate_visual_qa_plan_manifest(manifest)
    assert "visual_runtime_required must be false in S10" in errors


def test_s10_validator_rejects_external_model_dependency() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    manifest["external_model_allowed"] = True
    errors = validate_visual_qa_plan_manifest(manifest)
    assert "external_model_allowed must be false" in errors


def test_s10_validator_rejects_raw_pixel_payload_keys() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    manifest["plan"]["raw_pixels"] = "do-not-store-raw-pixels"
    errors = validate_visual_qa_plan_manifest(manifest)
    assert "forbidden visual QA payload key leaked: raw_pixels" in errors


def test_s10_validator_rejects_missing_required_check() -> None:
    manifest = build_visual_qa_plan_manifest("slides")
    manifest["plan"]["checks"] = [check for check in manifest["plan"]["checks"] if check["check_id"] != "contrast_risk"]
    errors = validate_visual_qa_plan_manifest(manifest)
    assert "missing planned visual QA check: contrast_risk" in errors


def test_s10_cli_outputs_json_for_slides_mode() -> None:
    result = run_s10_check("--mode", "slides", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["mode"] == "slides"


def test_s10_cli_outputs_json_for_artifact_mode() -> None:
    result = run_s10_check("--mode", "artifact", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["mode"] == "artifact"


def test_s10_cli_rejects_unknown_mode() -> None:
    result = run_s10_check("--mode", "browser", "--require-ready")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_s10_production_gate_contains_visual_qa_check() -> None:
    gate = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "Visual QA planning contract" in gate
    assert "scripts/kw_visual_qa_planning_check.py" in gate
