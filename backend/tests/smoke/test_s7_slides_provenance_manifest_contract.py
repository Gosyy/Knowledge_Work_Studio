from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.provenance_manifest_contract import (
    SLIDES_PROVENANCE_MANIFEST_CONTRACT,
    sample_generation_manifest,
    sample_retry_manifest,
    validate_manifest_payload,
    validate_slides_provenance_manifest_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_s7_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_provenance_manifest_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_s7_provenance_contract_is_ready() -> None:
    assert validate_slides_provenance_manifest_contract() == []
    assert SLIDES_PROVENANCE_MANIFEST_CONTRACT.offline_ready is True
    assert SLIDES_PROVENANCE_MANIFEST_CONTRACT.browser_policy == "none"
    assert SLIDES_PROVENANCE_MANIFEST_CONTRACT.source_to_artifact_links_required is True
    assert SLIDES_PROVENANCE_MANIFEST_CONTRACT.manifest_must_be_downloadable_artifact is True


def test_s7_generation_manifest_links_sources_plan_events_and_artifact() -> None:
    manifest = sample_generation_manifest()
    assert validate_manifest_payload(manifest, retry=False) == []
    assert manifest["plan_snapshot"]["plan_snapshot_id"] == "plansnap_contract_v1"
    assert manifest["render_attempt"]["render_mode"] == "adaptive"
    assert manifest["artifact"]["filename"].endswith(".pptx")
    assert any(event["event_type"] == "artifact.registered" for event in manifest["event_refs"])


def test_s7_retry_manifest_links_parent_and_new_artifact() -> None:
    manifest = sample_retry_manifest()
    assert validate_manifest_payload(manifest, retry=True) == []
    assert manifest["render_attempt"]["render_mode"] == "template"
    assert manifest["render_attempt"]["template_id"] == "board_review_local"
    assert manifest["retry_links"]["parent_plan_snapshot_id"] == "plansnap_contract_v1"
    assert manifest["retry_links"]["new_artifact_id"] == manifest["artifact"]["artifact_id"]


def test_s7_manifest_rejects_missing_required_event_refs() -> None:
    manifest = sample_generation_manifest()
    manifest["event_refs"] = []
    errors = validate_manifest_payload(manifest, retry=False)
    assert "missing event_ref: slides.plan.approved" in errors
    assert "missing event_ref: artifact.registered" in errors


def test_s7_manifest_rejects_template_without_template_id() -> None:
    manifest = sample_retry_manifest()
    manifest["render_attempt"].pop("template_id")
    errors = validate_manifest_payload(manifest, retry=True)
    assert "template render provenance must include template_id" in errors


def test_s7_manifest_rejects_forbidden_secret_or_raw_prompt_fields() -> None:
    manifest = sample_generation_manifest()
    manifest["raw_prompt"] = "do not store raw prompts in provenance manifests"
    manifest["sources"][0]["api_key"] = "do-not-store"
    errors = validate_manifest_payload(manifest, retry=False)
    assert any("forbidden raw secret/prompt fields" in error for error in errors)


def test_s7_cli_outputs_json_for_generation_mode() -> None:
    result = run_s7_check("--mode", "generation", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "generation"
    assert payload["sample_manifest"]["artifact"]["filename"].endswith(".pptx")


def test_s7_cli_outputs_json_for_retry_mode() -> None:
    result = run_s7_check("--mode", "retry", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["selected_mode"] == "retry"
    assert payload["sample_manifest"]["retry_links"]["parent_plan_snapshot_id"]


def test_s7_cli_rejects_unknown_mode() -> None:
    result = run_s7_check("--mode", "classic", "--require-ready")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_s7_gate_references_provenance_manifest_check() -> None:
    gate = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "Slides provenance manifest contract" in gate
    assert "kw_slides_provenance_manifest_check.py" in gate
