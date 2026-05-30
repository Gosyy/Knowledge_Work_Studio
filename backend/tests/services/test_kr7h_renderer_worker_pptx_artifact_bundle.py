from __future__ import annotations

import json
import subprocess
import tempfile
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
ARTIFACT_SCRIPT = WORKER_ROOT / "kw_renderer_worker_pptx_artifact_bundle_smoke.mjs"
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
        source_id="src_renderer_kr7h10_test",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h10_test",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h10_test")
    assert dry_run.status == "ready"
    return dry_run.as_dict()


def _run_artifact_bundle(output_dir: Path, payload: dict[str, object] | None = None) -> dict[str, object]:
    _ensure_worker_dependencies()
    command = ["node", str(ARTIFACT_SCRIPT), "--json", "--output-dir", str(output_dir)]
    stdin = None
    if payload is None:
        command.append("--fixture")
    else:
        command.append("--stdin")
        stdin = json.dumps(payload, ensure_ascii=False)
    completed = subprocess.run(command, input=stdin, cwd=WORKER_ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def _assert_common_ready_result(result: dict[str, object], output_dir: Path) -> None:
    assert result["schema_version"] == "presentation_renderer_worker_pptx_artifact_bundle.v1"
    assert result["render_report_schema_version"] == "presentation_renderer_worker_render_report.v1"
    assert result["status"] == "ready"
    assert result["dependency_name"] == "pptxgenjs"
    assert result["expected_dependency_version"] == "4.0.1"
    assert result["dependency_available"] is True
    assert result["dependency_version"] == "4.0.1"
    assert result["output_directory"] == str(output_dir.resolve())
    assert result["output_directory_exists"] is True
    assert result["mapped_fields"] == ["title", "body"]
    assert result["mapped_block_types"] == ["text"]
    assert result["mapped_slide_count"] >= 2
    assert isinstance(result["mapped_slide_ids"], list)
    assert len(result["mapped_slide_ids"]) >= 2
    assert result["persistent_artifact_written"] is True
    assert result["persistent_artifact_exists"] is True
    assert result["persistent_artifact_file_size_nonzero"] is True
    assert isinstance(result["persistent_artifact_size_bytes"], int)
    assert result["persistent_artifact_size_bytes"] > 0
    assert result["render_report_written"] is True
    assert result["render_report_exists"] is True
    assert result["render_report_file_size_nonzero"] is True
    assert isinstance(result["render_report_size_bytes"], int)
    assert result["render_report_size_bytes"] > 0
    assert result["render_report_deterministic"] is True
    assert result["artifact_bundle_produced"] is True
    assert result["artifact_bundle_verified"] is True
    assert result["presentation_ir_mapping_implemented"] is True
    assert result["title_body_mapping_implemented"] is True
    assert result["chart_mapping_implemented"] is False
    assert result["table_mapping_implemented"] is False
    assert result["image_mapping_implemented"] is False
    assert result["theme_mapping_implemented"] is False
    assert result["professional_layout_engine_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["issues"] == []

    pptx = output_dir / result["pptx_artifact_basename"]
    render_report = output_dir / result["render_report_basename"]
    assert pptx.is_file()
    assert pptx.stat().st_size == result["persistent_artifact_size_bytes"]
    assert render_report.is_file()
    report = json.loads(render_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "presentation_renderer_worker_render_report.v1"
    assert report["status"] == "ready"
    assert report["pptx_artifact_basename"] == result["pptx_artifact_basename"]
    assert report["mapped_fields"] == ["title", "body"]
    assert report["proof_bundle_produced"] is False
    assert report["libreoffice_executed"] is False
    assert report["visual_qa_executed"] is False


def test_kr7h10_artifact_bundle_fixture_writes_pptx_and_render_report() -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h10-test-") as tmp:
        output_dir = Path(tmp) / "bundle"
        result = _run_artifact_bundle(output_dir)
        _assert_common_ready_result(result, output_dir)


def test_kr7h10_artifact_bundle_accepts_source_backed_dry_run_payload() -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h10-test-") as tmp:
        output_dir = Path(tmp) / "bundle"
        result = _run_artifact_bundle(output_dir, _source_backed_dry_run_payload())
        _assert_common_ready_result(result, output_dir)
        assert result["input_schema_version"] == "presentation_renderer_worker_input.v1"
        assert "s001" in result["mapped_slide_ids"]
        assert "s002" in result["mapped_slide_ids"]


def test_kr7h10_artifact_bundle_report_stays_before_proof_runtime() -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h10-test-") as tmp:
        output_dir = Path(tmp) / "bundle"
        result = _run_artifact_bundle(output_dir, _source_backed_dry_run_payload())

    assert result["artifact_bundle_produced"] is True
    assert result["persistent_artifact_written"] is True
    assert result["filesystem_output_written"] is True
    assert result["production_pptx_output_implemented"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert "run_libreoffice_pdf_export" in result["blocked_runtime_actions"]
    assert "write_proof_bundle" in result["blocked_runtime_actions"]
    assert "no_pdf_png_proof_generation" in result["non_goals"]
    assert "no_visual_qa_scoring" in result["non_goals"]


def test_kr7h10_package_script_runs_with_cleanup_without_frontend_dependency_changes() -> None:
    _ensure_worker_dependencies()
    output_dir = WORKER_ROOT / ".kw-renderer-worker-artifact-bundle-smoke"
    if output_dir.exists():
        subprocess.run(["rm", "-rf", str(output_dir)], check=False)
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:artifact-bundle", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_pptx_artifact_bundle.v1"
    assert result["status"] == "ready"
    assert result["output_directory_cleanup_requested"] is True
    assert result["output_directory_cleanup_performed"] is True
    assert not output_dir.exists()

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text
