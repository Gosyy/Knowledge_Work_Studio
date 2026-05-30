from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "renderer_worker"
PACKAGE_JSON = WORKER_ROOT / "package.json"
PACKAGE_LOCK = WORKER_ROOT / "package-lock.json"
CONTRACT_DOC = WORKER_ROOT / "CONTRACT.md"
FRONTEND_PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"


def _package_json() -> dict[str, object]:
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))


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


def test_kr7h4_package_json_declares_isolated_renderer_worker_boundary() -> None:
    package = _package_json()

    assert package["name"] == "kw-studio-renderer-worker"
    assert package["private"] is True
    assert package["type"] == "module"
    assert "devDependencies" not in package
    assert "optionalDependencies" not in package
    assert "peerDependencies" not in package

    metadata = package["kwStudio"]
    assert isinstance(metadata, dict)
    assert metadata["schema_version"] == "presentation_renderer_worker_package_preflight.v1"
    assert metadata["renderer_worker_package_boundary"] is True
    assert metadata["frontend_package_boundary"] is False
    assert metadata["renderer_runtime_implemented"] is False
    assert metadata["production_pptx_output_implemented"] is False
    assert metadata["pptx_generation_executed"] is False
    assert metadata["artifact_bundle_produced"] is True
    assert metadata["proof_bundle_produced"] is True
    assert metadata["libreoffice_proof_bundle_smoke_implemented"] is True
    assert metadata["pptx_artifact_bundle_contract_implemented"] is True
    assert metadata["render_report_contract_implemented"] is True
    assert "no_frontend_package_changes" in metadata["non_goals"]


def test_kr7h5_package_declares_controlled_pptxgenjs_dependency_only_in_worker() -> None:
    package = _package_json()
    dependencies = package["dependencies"]
    assert dependencies == {"pptxgenjs": "4.0.1"}

    package_lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    assert package_lock["packages"][""]["dependencies"]["pptxgenjs"] == "4.0.1"
    assert package_lock["packages"]["node_modules/pptxgenjs"]["version"] == "4.0.1"

    metadata = package["kwStudio"]
    assert metadata["pptxgenjs_capability_schema_version"] == "presentation_renderer_worker_pptxgenjs_capability.v1"
    assert metadata["pptxgenjs_dependency_declared"] is True
    assert metadata["pptxgenjs_dependency_version"] == "4.0.1"
    assert metadata["pptxgenjs_capability_preflight_implemented"] is True
    assert metadata["pptxgenjs_in_memory_schema_version"] == "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"
    assert metadata["pptxgenjs_in_memory_preflight_implemented"] is True
    assert metadata["pptxgenjs_in_memory_object_created"] is True
    assert metadata["slide_content_added"] is False
    assert metadata["pptxgenjs_write_api_called"] is False
    assert metadata["filesystem_output_written"] is True
    assert metadata["empty_pptx_output_smoke_schema_version"] == "presentation_renderer_worker_empty_pptx_output_smoke.v1"
    assert metadata["empty_pptx_output_smoke_implemented"] is True
    assert metadata["temporary_pptx_write_api_called"] is True
    assert metadata["temporary_pptx_written"] is True
    assert metadata["temporary_pptx_deleted"] is True
    assert metadata["temporary_pptx_file_size_nonzero"] is True
    assert metadata["presentation_ir_mapping_implemented"] is True
    assert metadata["minimal_ir_mapping_smoke_schema_version"] == "presentation_renderer_worker_minimal_ir_mapping_smoke.v1"
    assert metadata["minimal_ir_mapping_smoke_implemented"] is True
    assert metadata["title_body_mapping_implemented"] is True
    assert metadata["mapped_fields"] == ["title", "body"]
    assert metadata["mapped_block_types"] == ["text"]
    assert metadata["single_slide_smoke_executed"] is True
    assert metadata["multi_slide_smoke_executed"] is True
    assert metadata["temporary_minimal_ir_pptx_written"] is True
    assert metadata["temporary_minimal_ir_pptx_deleted"] is True
    assert metadata["temporary_minimal_ir_pptx_file_size_nonzero"] is True
    assert metadata["chart_mapping_implemented"] is False
    assert metadata["table_mapping_implemented"] is False
    assert metadata["image_mapping_implemented"] is False
    assert metadata["professional_layout_engine_implemented"] is False
    assert metadata["persistent_artifact_written"] is True
    assert metadata["libreoffice_executed"] is True
    assert metadata["pdftoppm_executed"] is True
    assert metadata["libreoffice_proof_bundle_schema_version"] == "presentation_renderer_worker_libreoffice_proof_bundle.v1"
    assert metadata["libreoffice_proof_bundle_smoke_implemented"] is True
    assert metadata["libreoffice_required_for_proof_bundle"] is True
    assert metadata["pdftoppm_required_for_proof_bundle"] is True
    assert metadata["proof_bundle_produced"] is True
    assert metadata["proof_bundle_verified"] is True
    assert metadata["pdf_proof_written"] is True
    assert metadata["png_proofs_written"] is True
    assert metadata["fake_proof_used"] is False
    assert metadata["fallback_renderer_used"] is False
    assert metadata["python_pptx_proof_used"] is False
    assert metadata["visual_qa_executed"] is False
    assert metadata["artifact_bundle_schema_version"] == "presentation_renderer_worker_pptx_artifact_bundle.v1"
    assert metadata["render_report_schema_version"] == "presentation_renderer_worker_render_report.v1"
    assert metadata["pptx_artifact_bundle_contract_implemented"] is True
    assert metadata["render_report_contract_implemented"] is True
    assert metadata["artifact_bundle_produced"] is True
    assert metadata["artifact_bundle_verified"] is True
    assert metadata["render_report_written"] is True
    assert metadata["render_report_deterministic"] is True
    assert metadata["static_slide_output_smoke_schema_version"] == "presentation_renderer_worker_static_slide_output_smoke.v1"
    assert metadata["static_slide_output_smoke_implemented"] is True
    assert metadata["temporary_static_slide_pptx_write_api_called"] is True
    assert metadata["temporary_static_slide_pptx_written"] is True
    assert metadata["temporary_static_slide_pptx_deleted"] is True
    assert metadata["temporary_static_slide_pptx_file_size_nonzero"] is True
    assert metadata["static_slide_count"] == 1
    assert metadata["static_slide_content_added"] is True
    assert metadata["static_slide_uses_user_content"] is False
    assert metadata["static_slide_uses_presentation_ir"] is False


def test_kr7h4_package_scripts_run_protocol_preflight_without_runtime_output() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "check", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    protocol = subprocess.run(
        ["npm", "run", "protocol:preflight", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert protocol.returncode == 0, protocol.stdout + protocol.stderr
    capabilities = json.loads(protocol.stdout)
    assert capabilities["schema_version"] == "presentation_renderer_worker_protocol_preflight.v1"
    assert capabilities["renderer_runtime_implemented"] is False
    assert capabilities["production_pptx_output_implemented"] is False
    assert capabilities["artifact_bundle_produced"] is False
    assert capabilities["proof_bundle_produced"] is False
    assert "no_pptxgenjs_protocol_import" in capabilities["non_goals"]
    assert "generate_editable_pptx" in capabilities["blocked_runtime_actions"]


def test_kr7h5_package_scripts_run_dependency_capability_without_runtime_output() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "dependency:capability", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    capability = json.loads(completed.stdout)
    assert capability["schema_version"] == "presentation_renderer_worker_pptxgenjs_capability.v1"
    assert capability["status"] == "ready"
    assert capability["dependency_name"] == "pptxgenjs"
    assert capability["dependency_version"] == "4.0.1"
    assert capability["module_default_export_type"] == "function"
    assert capability["renderer_runtime_implemented"] is False
    assert capability["production_pptx_output_implemented"] is False
    assert capability["pptx_generation_executed"] is False
    assert capability["artifact_bundle_produced"] is False
    assert capability["proof_bundle_produced"] is False
    assert capability["output_mode"] == "dependency_capability_preflight_only"
    assert "write_pptx_file" in capability["blocked_runtime_actions"]
    assert capability["issues"] == []



def test_kr7h6_package_scripts_run_in_memory_preflight_without_output() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:in-memory", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"
    assert result["status"] == "ready"
    assert result["presentation_object_created"] is True
    assert result["slide_count"] == 0
    assert result["slide_content_added"] is False
    assert result["write_api_called"] is False
    assert result["filesystem_output_written"] is False
    assert result["renderer_runtime_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["pptx_generation_executed"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert "call_pptxgenjs_write_or_output_api" in result["blocked_runtime_actions"]


def test_kr7h7_package_scripts_run_empty_pptx_output_smoke_without_persistent_artifact() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:empty-output", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_empty_pptx_output_smoke.v1"
    assert result["status"] == "ready"
    assert result["temporary_pptx_written"] is True
    assert result["temporary_pptx_deleted"] is True
    assert result["temporary_pptx_file_size_nonzero"] is True
    assert result["slide_count"] == 0
    assert result["slide_content_added"] is False
    assert result["presentation_ir_mapping_implemented"] is False
    assert result["persistent_artifact_written"] is False
    assert result["filesystem_output_written"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["output_mode"] == "temporary_empty_pptx_output_smoke_only"



def test_kr7h8_package_scripts_run_static_slide_output_smoke_without_persistent_artifact() -> None:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:static-slide", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_static_slide_output_smoke.v1"
    assert result["status"] == "ready"
    assert result["temporary_pptx_written"] is True
    assert result["temporary_pptx_deleted"] is True
    assert result["temporary_pptx_file_size_nonzero"] is True
    assert result["static_slide_count"] == 1
    assert result["static_slide_content_added"] is True
    assert result["static_slide_uses_user_content"] is False
    assert result["static_slide_uses_presentation_ir"] is False
    assert result["presentation_ir_mapping_implemented"] is False
    assert result["persistent_artifact_written"] is False
    assert result["filesystem_output_written"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["output_mode"] == "temporary_static_single_slide_output_smoke_only"


def test_kr7h9_package_scripts_run_minimal_ir_mapping_smoke_without_persistent_artifact() -> None:
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
    assert result["mapped_fields"] == ["title", "body"]
    assert result["mapped_block_types"] == ["text"]
    assert result["single_slide_smoke_executed"] is True
    assert result["multi_slide_smoke_executed"] is True
    assert result["single_slide_pptx_written"] is True
    assert result["single_slide_pptx_deleted"] is True
    assert result["multi_slide_pptx_written"] is True
    assert result["multi_slide_pptx_deleted"] is True
    assert result["title_body_mapping_implemented"] is True
    assert result["presentation_ir_mapping_implemented"] is True
    assert result["chart_mapping_implemented"] is False
    assert result["table_mapping_implemented"] is False
    assert result["image_mapping_implemented"] is False
    assert result["professional_layout_engine_implemented"] is False
    assert result["persistent_artifact_written"] is False
    assert result["filesystem_output_written"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["output_mode"] == "temporary_minimal_ir_mapping_smoke_only"



def test_kr7h10_package_scripts_run_artifact_bundle_smoke_with_cleanup() -> None:
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
    assert result["render_report_schema_version"] == "presentation_renderer_worker_render_report.v1"
    assert result["mapped_fields"] == ["title", "body"]
    assert result["mapped_block_types"] == ["text"]
    assert result["mapped_slide_count"] >= 2
    assert result["persistent_artifact_written"] is True
    assert result["persistent_artifact_exists"] is True
    assert result["persistent_artifact_file_size_nonzero"] is True
    assert result["artifact_bundle_produced"] is True
    assert result["artifact_bundle_verified"] is True
    assert result["render_report_written"] is True
    assert result["render_report_exists"] is True
    assert result["render_report_file_size_nonzero"] is True
    assert result["render_report_deterministic"] is True
    assert result["output_directory_cleanup_requested"] is True
    assert result["output_directory_cleanup_performed"] is True
    assert result["presentation_ir_mapping_implemented"] is True
    assert result["title_body_mapping_implemented"] is True
    assert result["chart_mapping_implemented"] is False
    assert result["table_mapping_implemented"] is False
    assert result["image_mapping_implemented"] is False
    assert result["professional_layout_engine_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["output_mode"] == "persistent_pptx_artifact_bundle_and_render_report_contract_only"
    assert not output_dir.exists()


def test_kr7h4_package_contract_blocks_renderer_runtime_claims() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "presentation_renderer_worker_package_preflight.v1" in text
    assert "presentation_renderer_worker_pptxgenjs_capability.v1" in text
    assert "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1" in text
    assert "presentation_renderer_worker_empty_pptx_output_smoke.v1" in text
    assert "presentation_renderer_worker_static_slide_output_smoke.v1" in text
    assert "presentation_renderer_worker_minimal_ir_mapping_smoke.v1" in text
    assert "presentation_renderer_worker_pptx_artifact_bundle.v1" in text
    assert "presentation_renderer_worker_render_report.v1" in text
    assert "npm run protocol:preflight --prefix renderer_worker" in text
    assert "npm run dependency:capability --prefix renderer_worker" in text
    assert "npm run pptxgenjs:in-memory --prefix renderer_worker" in text
    assert "npm run pptxgenjs:empty-output --prefix renderer_worker" in text
    assert "npm run pptxgenjs:static-slide --prefix renderer_worker" in text
    assert "npm run pptxgenjs:minimal-ir-smoke --prefix renderer_worker" in text
    assert "npm run pptxgenjs:artifact-bundle --prefix renderer_worker" in text
    assert "renderer_runtime_implemented=false" in text
    assert "production_pptx_output_implemented=false" in text
    assert "pptx_generation_executed=false" in text
    assert "artifact_bundle_produced=false" in text
    assert "proof_bundle_produced=false" in text
    assert "slide_content_added=false" in text
    assert "pptxgenjs_write_api_called=false" in text
    assert "filesystem_output_written=false" in text
    assert "temporary_pptx_written=true" in text
    assert "temporary_pptx_deleted=true" in text
    assert "static_slide_count=1" in text
    assert "static_slide_content_added=true" in text
    assert "static_slide_uses_user_content=false" in text
    assert "static_slide_uses_presentation_ir=false" in text
    assert "minimal_ir_mapping_smoke_implemented=true" in text
    assert "title_body_mapping_implemented=true" in text
    assert "mapped_fields=title,body" in text
    assert "single_slide_smoke_executed=true" in text
    assert "multi_slide_smoke_executed=true" in text
    assert "persistent_artifact_written=false" in text
    assert "persistent_artifact_written=true" in text
    assert "artifact_bundle_produced=true" in text
    assert "render_report_written=true" in text
    assert "PptxGenJS is declared only inside the isolated renderer_worker package" in text
    assert "does not generate production PPTX" in text
    assert "does not write .pptx files" in text
    assert "temporary empty `.pptx`" in text
    assert "temporary `.pptx` containing exactly one fixed technical smoke slide" in text
    assert "maps only title/body text from validated renderer input" in text
    assert "does not run LibreOffice" in text
    assert "does not change UI" in text


def test_kr7h4_frontend_package_is_not_used_for_renderer_worker_boundary() -> None:
    frontend_package = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()

    assert "pptxgenjs" not in frontend_package
    assert "kw-studio-renderer-worker" not in frontend_package


def test_kr7h13_package_metadata_declares_closure_gate_without_production_claims() -> None:
    package = _package_json()
    metadata = package["kwStudio"]

    assert metadata["kr7h_closure_gate_schema_version"] == "presentation_renderer_worker_kr7h_closure_gate.v1"
    assert metadata["kr7h_closure_gate_implemented"] is True
    assert metadata["kr7h_phase_closed"] is True
    assert metadata["closed_through_phase"] == "KR-7H.13"
    assert metadata["kr7h_completed_phases"] == [
        "KR-7H.1",
        "KR-7H.2",
        "KR-7H.3",
        "KR-7H.4",
        "KR-7H.5",
        "KR-7H.6",
        "KR-7H.7",
        "KR-7H.8",
        "KR-7H.9",
        "KR-7H.10",
        "KR-7H.11",
        "KR-7H.12",
        "KR-7H.13",
    ]
    assert metadata["production_renderer_closure_implemented"] is False
    assert metadata["renderer_runtime_implemented"] is False
    assert metadata["production_pptx_output_implemented"] is False
    assert metadata["visual_qa_executed"] is False
    assert metadata["visual_quality_score"] is None
    assert metadata["kimi_level_quality_claimed"] is False
    assert metadata["source_image_selection_implemented"] is False
    assert metadata["image_mapping_implemented"] is False
    assert metadata["fake_artifacts_allowed"] is False
    assert metadata["fallback_renderer_allowed"] is False
    assert metadata["next_phase"] == "KR-7I template and brand understanding"
    assert "no_production_renderer_closure" in metadata["non_goals"]
    assert "no_kimi_level_quality_claim" in metadata["non_goals"]
