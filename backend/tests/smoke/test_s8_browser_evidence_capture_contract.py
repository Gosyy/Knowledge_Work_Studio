import json
import subprocess
import sys
from pathlib import Path

from backend.app.workflows.browser_evidence_capture_contract import (
    build_browser_evidence_manifest,
    build_browser_evidence_report,
    validate_browser_evidence_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_browser_evidence_capture_check.py"


def run_s8_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_s8_capture_manifest_is_ready_and_internal_only() -> None:
    report = build_browser_evidence_report("capture")
    manifest = report["manifest"]

    assert report["status"] == "ready"
    assert report["errors"] == []
    assert manifest["schema_version"] == "browser_evidence_capture_manifest.v1"
    assert manifest["workflow_id"] == "browser_assisted"
    assert manifest["offline_ready"] is True
    assert manifest["browser_policy"] == "internal_only"
    assert manifest["approval_required"] is True
    assert manifest["runtime_scope"] == "contract_only_no_autonomous_agent"
    assert manifest["capture"]["source"]["url_policy"] == "internal_only"
    assert manifest["capture"]["source"]["url_ref"].startswith("internal://")
    assert manifest["capture"]["operator_approval"]["status"] == "approved"


def test_s8_capture_manifest_has_required_events_and_bundle_metadata() -> None:
    report = build_browser_evidence_report("capture")
    manifest = report["manifest"]

    for event_name in report["required_capture_events"]:
        assert event_name in manifest["event_refs"]

    bundle = manifest["capture"]["evidence_bundle"]
    assert bundle["artifact_id"]
    assert bundle["storage_backend"] == "local"
    assert bundle["integrity"]["sha256"]
    assert isinstance(bundle["integrity"]["size_bytes"], int)


def test_s8_slides_link_manifest_connects_browser_evidence_to_s7_provenance() -> None:
    manifest = build_browser_evidence_manifest("slides_link")
    link = manifest["slides_provenance_link"]

    assert validate_browser_evidence_manifest(manifest) == []
    assert manifest["provenance_link"]["target_manifest_schema"] == "slides_provenance_manifest.v1"
    assert link["presentation_id"]
    assert link["generated_artifact_id"]
    assert link["provenance_manifest_artifact_id"]
    assert link["browser_evidence_artifact_ids"] == ["art_browser_evidence_bundle_s8"]
    assert link["source_links"][0]["source_type"] == "browser_evidence_bundle"
    assert link["retry_parent"]["is_retry"] is True
    assert link["retry_parent"]["parent_plan_snapshot_id"]


def test_s8_redaction_policy_is_safe_payload_only() -> None:
    manifest = build_browser_evidence_manifest("capture")
    policy = manifest["redaction_policy"]

    assert policy["safe_payload_only"] is True
    assert "secret" in policy["forbidden_payload_keys"]
    assert "raw_html" in policy["forbidden_payload_keys"]
    assert "screenshot_pixels" in policy["forbidden_payload_keys"]


def test_s8_validator_rejects_missing_operator_approval() -> None:
    manifest = build_browser_evidence_manifest("capture")
    manifest["capture"]["operator_approval"]["status"] = "pending"

    errors = validate_browser_evidence_manifest(manifest)

    assert "capture mode requires approved operator_approval" in errors


def test_s8_validator_rejects_non_internal_browser_source() -> None:
    manifest = build_browser_evidence_manifest("capture")
    manifest["capture"]["source"]["url_policy"] = "public_internet"

    errors = validate_browser_evidence_manifest(manifest)

    assert "capture.source.url_policy must be internal_only or intranet_only" in errors


def test_s8_validator_rejects_missing_slides_provenance_artifact_link() -> None:
    manifest = build_browser_evidence_manifest("slides_link")
    manifest["slides_provenance_link"]["provenance_manifest_artifact_id"] = ""

    errors = validate_browser_evidence_manifest(manifest)

    assert "slides_provenance_link.provenance_manifest_artifact_id is required" in errors


def test_s8_validator_rejects_payload_secret_key_outside_policy_catalog() -> None:
    manifest = build_browser_evidence_manifest("capture")
    manifest["capture"]["safe_metadata"] = {"secret": "must-not-be-here"}

    errors = validate_browser_evidence_manifest(manifest)

    assert "forbidden evidence payload key leaked: secret" in errors


def test_s8_cli_outputs_json_for_capture_mode() -> None:
    result = run_s8_check("--mode", "capture", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["errors"] == []


def test_s8_cli_outputs_json_for_slides_link_mode() -> None:
    result = run_s8_check("--mode", "slides_link", "--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["errors"] == []


def test_s8_production_gate_contains_browser_evidence_check() -> None:
    gate = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "scripts/kw_browser_evidence_capture_check.py" in gate
    assert "Browser evidence capture contract" in gate
    assert "Browser evidence slides provenance link contract" in gate
