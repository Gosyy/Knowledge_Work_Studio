from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "renderer_worker"
EMPTY_OUTPUT_SCRIPT = WORKER_ROOT / "kw_renderer_worker_empty_pptx_output_smoke.mjs"
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


def _run_empty_output() -> dict[str, object]:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["node", str(EMPTY_OUTPUT_SCRIPT), "--json"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_kr7h7_empty_output_smoke_writes_and_deletes_temporary_pptx() -> None:
    result = _run_empty_output()

    assert result["schema_version"] == "presentation_renderer_worker_empty_pptx_output_smoke.v1"
    assert result["status"] == "ready"
    assert result["dependency_name"] == "pptxgenjs"
    assert result["expected_dependency_version"] == "4.0.1"
    assert result["dependency_available"] is True
    assert result["dependency_version"] == "4.0.1"
    assert result["module_default_export_type"] == "function"
    assert result["module_default_export_name"] == "PptxGenJS"
    assert result["empty_pptx_output_smoke_implemented"] is True
    assert result["temporary_pptx_write_api_called"] is True
    assert result["temporary_pptx_written"] is True
    assert result["temporary_pptx_deleted"] is True
    assert result["temporary_directory_removed"] is True
    assert result["temporary_output_basename"] == "kr7h7-empty-output-smoke.pptx"
    assert isinstance(result["temporary_pptx_file_size_bytes"], int)
    assert result["temporary_pptx_file_size_bytes"] > 0
    assert result["temporary_pptx_file_size_nonzero"] is True
    assert result["slide_count"] == 0
    assert result["issues"] == []


def test_kr7h7_empty_output_smoke_contract_blocks_persistent_artifacts() -> None:
    result = _run_empty_output()

    assert result["slide_content_added"] is False
    assert result["presentation_ir_mapping_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["renderer_runtime_implemented"] is False
    assert result["persistent_artifact_written"] is False
    assert result["filesystem_output_written"] is False
    assert result["pptx_generation_executed"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert result["libreoffice_executed"] is False
    assert result["visual_qa_executed"] is False
    assert result["output_mode"] == "temporary_empty_pptx_output_smoke_only"
    assert "map_presentation_ir_to_slides" in result["blocked_runtime_actions"]
    assert "persist_pptx_artifact" in result["blocked_runtime_actions"]
    assert "run_libreoffice_pdf_export" in result["blocked_runtime_actions"]
    assert "write_artifact_bundle" in result["blocked_runtime_actions"]
    assert "no_presentation_ir_mapping" in result["non_goals"]
    assert "no_persistent_filesystem_output" in result["non_goals"]
    assert "no_production_pptx_generation" in result["non_goals"]


def test_kr7h7_package_check_runs_empty_output_without_frontend_changes() -> None:
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
    assert result["temporary_pptx_deleted"] is True
    assert result["persistent_artifact_written"] is False

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text
