from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "renderer_worker"
CAPABILITY_SCRIPT = WORKER_ROOT / "kw_renderer_worker_pptxgenjs_capability.mjs"
FRONTEND_PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"


def _ensure_worker_dependencies() -> None:
    completed = subprocess.run(
        ["npm", "ci", "--ignore-scripts", "--audit=false", "--fund=false", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _run_capability() -> dict[str, object]:
    _ensure_worker_dependencies()
    completed = subprocess.run(
        ["node", str(CAPABILITY_SCRIPT), "--json"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_kr7h5_capability_script_reports_pinned_pptxgenjs_without_generation() -> None:
    result = _run_capability()

    assert result["schema_version"] == "presentation_renderer_worker_pptxgenjs_capability.v1"
    assert result["status"] == "ready"
    assert result["dependency_name"] == "pptxgenjs"
    assert result["expected_dependency_version"] == "4.0.1"
    assert result["dependency_available"] is True
    assert result["dependency_version"] == "4.0.1"
    assert result["module_default_export_type"] == "function"
    assert result["renderer_runtime_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["pptx_generation_executed"] is False
    assert result["output_mode"] == "dependency_capability_preflight_only"
    assert result["issues"] == []


def test_kr7h5_package_keeps_dependency_isolated_from_frontend() -> None:
    worker_package = json.loads((WORKER_ROOT / "package.json").read_text(encoding="utf-8"))
    assert worker_package["dependencies"] == {"pptxgenjs": "4.0.1"}

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text


def test_kr7h5_capability_contract_blocks_runtime_and_artifact_claims() -> None:
    result = _run_capability()

    assert result["artifact_bundle_produced"] is False
    assert result["proof_bundle_produced"] is False
    assert "generate_editable_pptx" in result["blocked_runtime_actions"]
    assert "write_pptx_file" in result["blocked_runtime_actions"]
    assert "run_libreoffice_pdf_export" in result["blocked_runtime_actions"]
    assert "write_artifact_bundle" in result["blocked_runtime_actions"]
    assert "no_pptx_generation" in result["non_goals"]
    assert "no_libreoffice_execution" in result["non_goals"]
    assert "no_visual_qa_scoring" in result["non_goals"]
