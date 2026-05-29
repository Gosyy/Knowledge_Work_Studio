from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

from backend.app.services.slides_service import (
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_dry_run_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_SCRIPT = REPO_ROOT / "renderer_worker" / "kw_renderer_worker_protocol_preflight.mjs"


def _source_backed_dry_run_payload() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_protocol",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h3",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_protocol")
    assert dry_run.status == "ready"
    return dry_run.as_dict()


def _run_protocol(payload: dict[str, object] | None = None, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["node", str(PROTOCOL_SCRIPT), *args]
    stdin = None if payload is None else json.dumps(payload, ensure_ascii=False)
    return subprocess.run(command, input=stdin, text=True, capture_output=True, check=False)


def test_kr7h3_protocol_capabilities_are_preflight_only() -> None:
    completed = _run_protocol(None, "--capabilities")

    assert completed.returncode == 0, completed.stderr
    capabilities = json.loads(completed.stdout)
    assert capabilities["schema_version"] == "presentation_renderer_worker_protocol_preflight.v1"
    assert capabilities["protocol_runtime_implemented"] is True
    assert capabilities["renderer_runtime_implemented"] is False
    assert capabilities["production_pptx_output_implemented"] is False
    assert capabilities["artifact_bundle_produced"] is False
    assert capabilities["proof_bundle_produced"] is False
    assert "no_pptxgenjs_protocol_import" in capabilities["non_goals"]
    assert "import_or_execute_pptxgenjs" in capabilities["blocked_runtime_actions"]


def test_kr7h3_protocol_accepts_ready_dry_run_payload_without_runtime_output() -> None:
    completed = _run_protocol(_source_backed_dry_run_payload())

    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_protocol_preflight_response.v1"
    assert result["protocol_schema_version"] == "presentation_renderer_worker_protocol_preflight.v1"
    assert result["status"] == "ready"
    assert result["renderer_runtime_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["output_mode"] == "protocol_preflight_only"
    assert result["input_summary"]["slide_count"] >= 1
    assert "generate_editable_pptx" in result["blocked_runtime_actions"]
    assert result["issues"] == []


def test_kr7h3_protocol_blocks_prompt_only_dry_run_payload() -> None:
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h3_blocked",
            title="Draft without sources",
            objective="Do not render without evidence",
            require_evidence=False,
            slide_count=3,
        ),
        OfflineEvidenceIndexBuilder().build_index([]),
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir).as_dict()

    completed = _run_protocol(dry_run)

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert "dry_run_not_ready" in {issue["code"] for issue in result["issues"]}
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False


def test_kr7h3_protocol_rejects_runtime_and_bundle_claims() -> None:
    payload = deepcopy(_source_backed_dry_run_payload())
    payload["renderer_runtime_implemented"] = True
    payload["artifact_bundle_produced"] = True
    assert isinstance(payload["renderer_input"], dict)
    payload["renderer_input"]["artifact_bundle_produced"] = True
    assert isinstance(payload["invocation_manifest"], dict)
    payload["invocation_manifest"]["proof_bundle_produced"] = True

    completed = _run_protocol(payload)

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    codes = {issue["code"] for issue in result["issues"]}
    assert "runtime_claim_not_allowed" in codes
    assert "artifact_bundle_claim_not_allowed" in codes
    assert "renderer_input_bundle_claim_not_allowed" in codes
    assert "invocation_bundle_claim_not_allowed" in codes


def test_kr7h3_protocol_rejects_invalid_json_fail_closed() -> None:
    completed = subprocess.run(
        ["node", str(PROTOCOL_SCRIPT)],
        input="{not-json",
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert result["issues"][0]["code"] == "invalid_json_input"
    assert result["renderer_runtime_implemented"] is False
