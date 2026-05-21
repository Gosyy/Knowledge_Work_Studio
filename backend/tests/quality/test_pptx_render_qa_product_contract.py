from __future__ import annotations

import contextlib
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from backend.app.services.slides_service.kq_deck_quality import assess_kq1a_deck_artifact_bundle, read_json
from backend.app.services.slides_service.kq_exec_memo_deck_generation import generate_kq1b_exec_memo_deck_bundle
from backend.app.services.slides_service.kq_pptx_render_qa import (
    KQ1C_CONTROLLED_SCOPE_FLAGS,
    build_kq1c_capabilities_report,
    run_kq1c_independent_render_qa,
)


def _office_render_stack_available() -> bool:
    return bool(shutil.which("soffice") or shutil.which("libreoffice")) and bool(shutil.which("pdftoppm"))


def _supported_render_mode() -> str:
    if _office_render_stack_available():
        return "libreoffice"
    pytest.importorskip("pptx")
    pytest.importorskip("PIL")
    return "python-pptx-text"


@contextlib.contextmanager
def _portable_render_tmp_path(tmp_path: Path):
    if _office_render_stack_available():
        root = Path.cwd() / "logs" / "product-pptx-render-qa-pytest"
        root.mkdir(parents=True, exist_ok=True)
        yield Path(tempfile.mkdtemp(prefix="case-", dir=str(root)))
    else:
        yield tmp_path


def test_pptx_render_qa_capability_contract_is_portable_and_conservative() -> None:
    report = build_kq1c_capabilities_report()
    assert report["independent_pptx_render_qa_supported"] is True
    assert report["python_pptx_text_render_fallback_supported"] is True
    assert report["kimi_level_claimed_by_kq1c"] is False
    supported_stack = report["office_render_stack_available"] or (report["python_pptx_available"] and report["pillow_available"])
    if not supported_stack:
        pytest.skip("PPTX render stack is not installed on this machine; targeted render evidence still requires a render stack.")
    assert supported_stack is True


def test_pptx_render_qa_enhances_exec_memo_bundle_when_render_stack_is_available(tmp_path: Path) -> None:
    with _portable_render_tmp_path(tmp_path) as work:
        kq1b_zip = work / "kq1b.zip"
        generate_kq1b_exec_memo_deck_bundle(work / "kq1b", zip_out=kq1b_zip)
        out_zip = work / "kq1c.zip"
        result = run_kq1c_independent_render_qa(kq1b_zip, work / "kq1c", zip_out=out_zip, render_mode=_supported_render_mode())
    assert result.status == "ready"
    assert result.independent_pptx_render_performed_by_kq1c is True
    assert result.render_engine in {"python_pptx_text_renderer", "libreoffice_pdf_pdftoppm"}
    assert result.rendered_slide_count == result.slide_count_from_pptx
    assert result.empty_slide_count == 0
    assert result.text_overflow_count == 0
    assert result.tiny_text_count == 0
    assert result.kq1a_status_after_kq1c == "ready"
    with zipfile.ZipFile(out_zip, "r") as archive:
        names = set(archive.namelist())
    assert "kq1c_render_manifest.json" in names
    assert "kq1c_visual_qa_report.json" in names
    assert "independent_rendered_slides/slide_01.png" in names
    assert "review_packet.json" in names
    assessment = assess_kq1a_deck_artifact_bundle(out_zip)
    assert assessment.status == "ready"


def test_pptx_render_qa_preserves_conservative_claim_boundaries(tmp_path: Path) -> None:
    with _portable_render_tmp_path(tmp_path) as work:
        kq1b_zip = work / "kq1b.zip"
        generate_kq1b_exec_memo_deck_bundle(work / "kq1b", zip_out=kq1b_zip)
        result = run_kq1c_independent_render_qa(kq1b_zip, work / "kq1c", render_mode=_supported_render_mode())
    manifest = read_json(Path(result.output_bundle_dir) / "kq1c_render_manifest.json")
    visual = read_json(Path(result.output_bundle_dir) / "kq1c_visual_qa_report.json")
    assert result.selected_offline_workflow_parity_claim_supported_after_kq1c is False
    assert result.kimi_level_claimed_by_kq1c is False
    assert result.server3_local_intranet_route_verified_by_kq1c is False
    assert visual["human_review_decision"] is None
    for key, expected in KQ1C_CONTROLLED_SCOPE_FLAGS.items():
        assert manifest["controlled_scope"][key] is expected
