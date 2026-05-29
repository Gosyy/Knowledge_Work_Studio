from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "renderer_worker"
IN_MEMORY_SCRIPT = WORKER_ROOT / "kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs"
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


def _run_in_memory() -> dict[str, object]:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["node", str(IN_MEMORY_SCRIPT), "--json"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_kr7h6_in_memory_preflight_constructs_object_without_output() -> None:
    result = _run_in_memory()

    assert result["schema_version"] == "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"
    assert result["status"] == "ready"
    assert result["dependency_name"] == "pptxgenjs"
    assert result["expected_dependency_version"] == "4.0.1"
    assert result["dependency_available"] is True
    assert result["dependency_version"] == "4.0.1"
    assert result["module_default_export_type"] == "function"
    assert result["module_default_export_name"] == "PptxGenJS"
    assert result["in_memory_preflight_implemented"] is True
    assert result["presentation_object_created"] is True
    assert result["presentation_object_type"] == "PptxGenJS"
    assert result["slide_count"] == 0
    assert result["slide_content_added"] is False
    assert result["write_api_called"] is False
    assert result["filesystem_output_written"] is False
    assert result["output_mode"] == "in_memory_construction_preflight_only"
    assert result["issues"] == []


def test_kr7h6_in_memory_preflight_contract_blocks_write_and_artifact_claims() -> None:
    result = _run_in_memory()

    assert result["renderer_runtime_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["pptx_generation_executed"] is False
    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert "call_pptxgenjs_write_or_output_api" in result["blocked_runtime_actions"]
    assert "write_pptx_file" in result["blocked_runtime_actions"]
    assert "map_presentation_ir_to_slides" in result["blocked_runtime_actions"]
    assert "write_artifact_bundle" in result["blocked_runtime_actions"]
    assert "no_pptx_generation" in result["non_goals"]
    assert "no_presentation_ir_mapping" in result["non_goals"]
    assert "no_pptxgenjs_write_or_output_calls" in result["non_goals"]
    assert "no_filesystem_output" in result["non_goals"]


def test_kr7h6_package_check_runs_in_memory_script_without_frontend_changes() -> None:
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

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text
