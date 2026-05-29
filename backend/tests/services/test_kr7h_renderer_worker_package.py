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


def _ensure_worker_dependencies() -> None:
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
    assert metadata["artifact_bundle_produced"] is False
    assert metadata["proof_bundle_produced"] is False
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


def test_kr7h4_package_contract_blocks_renderer_runtime_claims() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "presentation_renderer_worker_package_preflight.v1" in text
    assert "presentation_renderer_worker_pptxgenjs_capability.v1" in text
    assert "npm run protocol:preflight --prefix renderer_worker" in text
    assert "npm run dependency:capability --prefix renderer_worker" in text
    assert "renderer_runtime_implemented=false" in text
    assert "production_pptx_output_implemented=false" in text
    assert "pptx_generation_executed=false" in text
    assert "artifact_bundle_produced=false" in text
    assert "proof_bundle_produced=false" in text
    assert "PptxGenJS is declared only inside the isolated renderer_worker package" in text
    assert "does not generate production PPTX" in text
    assert "does not run LibreOffice" in text
    assert "does not change UI" in text


def test_kr7h4_frontend_package_is_not_used_for_renderer_worker_boundary() -> None:
    frontend_package = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()

    assert "pptxgenjs" not in frontend_package
    assert "kw-studio-renderer-worker" not in frontend_package
