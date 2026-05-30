from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.app.services.slides_service import (
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_dry_run_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "renderer_worker"
MINIMAL_MAPPING_SCRIPT = WORKER_ROOT / "kw_renderer_worker_minimal_ir_mapping_smoke.mjs"
FRONTEND_PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"


def _worker_dependency_tree_ready() -> bool:
    return (WORKER_ROOT / "node_modules" / "pptxgenjs" / "package.json").is_file()


def _ensure_worker_dependencies() -> None:
    if _worker_dependency_tree_ready():
        return
    completed = subprocess.run(
        ["npm", "ci", "--ignore-scripts", "--audit=false", "--fund=false", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _source_backed_dry_run_payload() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h9_test",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h9_test",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h9_test")
    assert dry_run.status == "ready"
    return dry_run.as_dict()


def _run_minimal_mapping(payload: dict[str, object] | None = None) -> dict[str, object]:
    _ensure_worker_dependencies()
    command = ["node", str(MINIMAL_MAPPING_SCRIPT), "--json"]
    stdin = None
    if payload is None:
        command.append("--fixture")
    else:
        command.append("--stdin")
        stdin = json.dumps(payload, ensure_ascii=False)
    completed = subprocess.run(command, input=stdin, cwd=WORKER_ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def _assert_common_ready_result(result: dict[str, object]) -> None:
    assert result["schema_version"] == "presentation_renderer_worker_minimal_ir_mapping_smoke.v1"
    assert result["status"] == "ready"
    assert result["dependency_name"] == "pptxgenjs"
    assert result["expected_dependency_version"] == "4.0.1"
    assert result["dependency_available"] is True
    assert result["dependency_version"] == "4.0.1"
    assert result["minimal_ir_mapping_smoke_implemented"] is True
    assert result["renderer_input_schema_version"] == "presentation_renderer_worker_input.v1"
    assert result["input_status"] == "ready"
    assert result["mapped_fields"] == ["title", "body"]
    assert result["mapped_block_types"] == ["text"]
    assert isinstance(result["mapped_slide_ids"], list)
    assert len(result["mapped_slide_ids"]) >= 2
    assert result["mapped_slide_count"] >= 2
    assert result["single_slide_smoke_executed"] is True
    assert result["multi_slide_smoke_executed"] is True
    assert result["single_slide_pptx_written"] is True
    assert result["single_slide_pptx_deleted"] is True
    assert result["single_slide_file_size_nonzero"] is True
    assert isinstance(result["single_slide_file_size_bytes"], int)
    assert result["single_slide_file_size_bytes"] > 0
    assert result["multi_slide_pptx_written"] is True
    assert result["multi_slide_pptx_deleted"] is True
    assert result["multi_slide_file_size_nonzero"] is True
    assert isinstance(result["multi_slide_file_size_bytes"], int)
    assert result["multi_slide_file_size_bytes"] > 0
    assert result["temporary_directory_removed"] is True
    assert result["issues"] == []


def test_kr7h9_minimal_ir_mapping_fixture_runs_single_and_multi_slide_smoke() -> None:
    result = _run_minimal_mapping()

    _assert_common_ready_result(result)
    assert result["mapped_slide_ids"] == ["s001", "s002"]
    assert result["output_mode"] == "temporary_minimal_ir_mapping_smoke_only"


def test_kr7h9_minimal_ir_mapping_accepts_source_backed_dry_run_payload() -> None:
    result = _run_minimal_mapping(_source_backed_dry_run_payload())

    _assert_common_ready_result(result)
    assert result["input_schema_version"] == "presentation_renderer_worker_input.v1"
    assert "s001" in result["mapped_slide_ids"]
    assert "s002" in result["mapped_slide_ids"]


def test_kr7h9_minimal_ir_mapping_remains_temporary_and_not_artifact_runtime() -> None:
    result = _run_minimal_mapping(_source_backed_dry_run_payload())

    assert result["title_body_mapping_implemented"] is True
    assert result["presentation_ir_mapping_implemented"] is True
    assert result["chart_mapping_implemented"] is False
    assert result["table_mapping_implemented"] is False
    assert result["image_mapping_implemented"] is False
    assert result["theme_mapping_implemented"] is False
    assert result["professional_layout_engine_implemented"] is False
    assert result["user_prompt_passthrough_allowed"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["renderer_runtime_implemented"] is False
    assert result["persistent_artifact_written"] is False
    assert result["filesystem_output_written"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert "persist_pptx_artifact" in result["blocked_runtime_actions"]
    assert "map_charts_tables_images" in result["blocked_runtime_actions"]
    assert "run_libreoffice_pdf_export" in result["blocked_runtime_actions"]
    assert "write_artifact_bundle" in result["blocked_runtime_actions"]
    assert "no_persistent_pptx_artifact" in result["non_goals"]
    assert "no_charts_tables_images_mapping" in result["non_goals"]


def test_kr7h9_package_script_runs_without_frontend_dependency_changes() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:minimal-ir-smoke", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_minimal_ir_mapping_smoke.v1"
    assert result["status"] == "ready"
    assert result["single_slide_smoke_executed"] is True
    assert result["multi_slide_smoke_executed"] is True
    assert result["persistent_artifact_written"] is False

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text
