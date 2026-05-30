from __future__ import annotations

import json
import shutil
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
PROOF_SCRIPT = WORKER_ROOT / "kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs"
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


def _office_render_stack_available() -> bool:
    return bool(shutil.which("soffice") or shutil.which("libreoffice")) and bool(shutil.which("pdftoppm"))


def _source_backed_dry_run_payload() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h11_test",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h11_test",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h11_test")
    assert dry_run.status == "ready"
    return dry_run.as_dict()


def _run_proof_bundle(output_dir: Path, payload: dict[str, object] | None = None) -> dict[str, object]:
    _ensure_worker_dependencies()
    assert _office_render_stack_available(), "LibreOffice/soffice and pdftoppm are required for KR-7H.11 ready proof evidence"
    command = ["node", str(PROOF_SCRIPT), "--json", "--output-dir", str(output_dir)]
    stdin = None
    if payload is None:
        command.append("--fixture")
    else:
        command.append("--stdin")
        stdin = json.dumps(payload, ensure_ascii=False)
    completed = subprocess.run(command, input=stdin, cwd=WORKER_ROOT, text=True, capture_output=True, check=False, timeout=240)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def _assert_common_ready_result(result: dict[str, object], output_dir: Path) -> None:
    assert result["schema_version"] == "presentation_renderer_worker_libreoffice_proof_bundle.v1"
    assert result["artifact_bundle_schema_version"] == "presentation_renderer_worker_pptx_artifact_bundle.v1"
    assert result["render_report_schema_version"] == "presentation_renderer_worker_render_report.v1"
    assert result["proof_bundle_schema_version"] == "presentation_renderer_worker_libreoffice_proof_bundle.v1"
    assert result["status"] == "ready"
    assert result["artifact_bundle_produced"] is True
    assert result["artifact_bundle_verified"] is True
    assert result["upstream_artifact_bundle_status"] == "ready"
    assert result["proof_bundle_written"] is True
    assert result["proof_bundle_exists"] is True
    assert result["proof_bundle_file_size_nonzero"] is True
    assert result["proof_bundle_produced"] is True
    assert result["proof_bundle_verified"] is True
    assert result["proof_bundle_deterministic"] is True
    assert result["libreoffice_required"] is True
    assert result["pdftoppm_required"] is True
    assert result["libreoffice_available"] is True
    assert result["pdftoppm_available"] is True
    assert result["libreoffice_executed"] is True
    assert result["pdftoppm_executed"] is True
    assert result["pdf_proof_written"] is True
    assert result["pdf_proof_exists"] is True
    assert result["pdf_proof_file_size_nonzero"] is True
    assert result["png_proofs_written"] is True
    assert isinstance(result["png_proof_count"], int)
    assert result["png_proof_count"] >= 1
    assert result["mapped_fields"] == ["title", "body"]
    assert result["mapped_block_types"] == ["text"]
    assert len(result["mapped_slide_ids"]) >= 2
    assert result["title_body_mapping_implemented"] is True
    assert result["presentation_ir_mapping_implemented"] is True
    assert result["chart_mapping_implemented"] is False
    assert result["table_mapping_implemented"] is False
    assert result["image_mapping_implemented"] is False
    assert result["theme_mapping_implemented"] is False
    assert result["professional_layout_engine_implemented"] is False
    assert result["production_pptx_output_implemented"] is False
    assert result["renderer_runtime_implemented"] is False
    assert result["visual_qa_executed"] is False
    assert result["visual_quality_score"] is None
    assert result["fake_proof_used"] is False
    assert result["fallback_renderer_used"] is False
    assert result["python_pptx_proof_used"] is False
    assert result["issues"] == []

    expected_files = [
        result["pptx_artifact_basename"],
        result["render_report_basename"],
        result["pdf_proof_basename"],
        result["proof_bundle_basename"],
    ]
    for basename in expected_files:
        path = output_dir / str(basename)
        assert path.is_file()
        assert path.stat().st_size > 0
    proof_dir = output_dir / str(result["png_proof_directory"])
    assert proof_dir.is_dir()
    for basename in result["png_proof_basenames"]:
        path = proof_dir / str(basename)
        assert path.is_file()
        assert path.stat().st_size > 0

    proof_payload = json.loads((output_dir / str(result["proof_bundle_basename"])).read_text(encoding="utf-8"))
    assert proof_payload["schema_version"] == result["schema_version"]
    assert proof_payload["status"] == "ready"
    assert proof_payload["fake_proof_used"] is False
    assert proof_payload["fallback_renderer_used"] is False


def test_kr7h11_livreoffice_proof_bundle_fixture_writes_pdf_png_and_json() -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h11-test-") as tmp:
        output_dir = Path(tmp) / "bundle"
        result = _run_proof_bundle(output_dir)
        _assert_common_ready_result(result, output_dir)


def test_kr7h11_livreoffice_proof_bundle_accepts_source_backed_dry_run_payload() -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h11-test-") as tmp:
        output_dir = Path(tmp) / "bundle"
        result = _run_proof_bundle(output_dir, _source_backed_dry_run_payload())
        _assert_common_ready_result(result, output_dir)
        assert result["input_schema_version"] == "presentation_renderer_worker_dry_run.v1"
        assert "s001" in result["mapped_slide_ids"]
        assert "s002" in result["mapped_slide_ids"]


def test_kr7h11_missing_libreoffice_fails_closed_without_fake_proof() -> None:
    _ensure_worker_dependencies()
    with tempfile.TemporaryDirectory(prefix="kw-kr7h11-test-missing-") as tmp:
        output_dir = Path(tmp) / "bundle"
        missing = Path(tmp) / "missing-soffice"
        completed = subprocess.run(
            [
                "node",
                str(PROOF_SCRIPT),
                "--json",
                "--fixture",
                "--output-dir",
                str(output_dir),
                "--soffice-bin",
                str(missing),
            ],
            cwd=WORKER_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        assert completed.returncode != 0
        result = json.loads(completed.stdout)
    assert result["status"] == "blocked"
    assert result["libreoffice_available"] is False
    assert result["libreoffice_executed"] is False
    assert result["proof_bundle_produced"] is False
    assert result["proof_bundle_verified"] is False
    assert result["fake_proof_used"] is False
    assert result["fallback_renderer_used"] is False
    assert result["python_pptx_proof_used"] is False
    assert {issue["code"] for issue in result["issues"]} == {"libreoffice_unavailable"}


def test_kr7h11_package_script_runs_with_cleanup_without_frontend_dependency_changes() -> None:
    _ensure_worker_dependencies()
    assert _office_render_stack_available(), "LibreOffice/soffice and pdftoppm are required for KR-7H.11 ready proof evidence"
    output_dir = WORKER_ROOT / ".kw-renderer-worker-libreoffice-proof-bundle-smoke"
    if output_dir.exists():
        subprocess.run(["rm", "-rf", str(output_dir)], check=False)
    completed = subprocess.run(
        ["npm", "run", "pptxgenjs:libreoffice-proof-bundle", "--silent"],
        cwd=WORKER_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["schema_version"] == "presentation_renderer_worker_libreoffice_proof_bundle.v1"
    assert result["status"] == "ready"
    assert result["proof_bundle_produced"] is True
    assert result["output_directory_cleanup_requested"] is True
    assert not output_dir.exists()

    frontend_text = FRONTEND_PACKAGE_JSON.read_text(encoding="utf-8").lower()
    assert "pptxgenjs" not in frontend_text
    assert "kw-studio-renderer-worker" not in frontend_text
