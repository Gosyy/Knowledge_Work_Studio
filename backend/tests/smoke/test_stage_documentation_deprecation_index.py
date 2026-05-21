from pathlib import Path

from scripts.kw_stage_docs_deprecation_check import build_report


def _write(path: Path, text: str = "ready\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_required_docs(repo: Path) -> None:
    for path in (
        "docs/product/PRODUCT_VISION.md",
        "docs/product/USER_WORKFLOWS.md",
        "docs/product/ARTIFACT_MODEL.md",
        "docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md",
        "docs/workflows/DOCX_WORKFLOW.md",
        "docs/workflows/PDF_WORKFLOW.md",
        "docs/workflows/XLSX_WORKFLOW.md",
        "docs/workflows/SLIDES_WORKFLOW.md",
        "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
        "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
        "docs/quality/QUALITY_GATES.md",
        "docs/quality/XLSX_VALIDATION.md",
        "docs/quality/RENDER_AND_VISUAL_QA.md",
        "docs/operators/LOCAL_DEVELOPMENT.md",
    ):
        _write(repo / path, "canonical product docs\n")

    policy_text = (
        "docs/codex remains temporarily for legacy tests/checkers\n"
        "KR-2\n"
        "Canonical product docs\n"
    )
    _write(repo / "docs/archive/development-history/README.md", policy_text)
    _write(repo / "docs/refactor/STAGE_DOCUMENTATION_DEPRECATION_INDEX.md", policy_text)


def test_deprecation_report_is_ready_with_legacy_codex_docs(tmp_path: Path) -> None:
    _seed_required_docs(tmp_path)
    _write(tmp_path / "docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md", "legacy stage doc\n")

    report = build_report(tmp_path)

    assert report.status == "ready"
    assert report.legacy_stage_docs_count == 1
    assert report.physical_archive_blocked_until.startswith("KR-2")


def test_deprecation_report_blocks_machine_specific_policy_docs(tmp_path: Path) -> None:
    _seed_required_docs(tmp_path)
    _write(tmp_path / "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md", "legacy stage doc\n")
    _write(
        tmp_path / "docs/refactor/STAGE_DOCUMENTATION_DEPRECATION_INDEX.md",
        "docs/codex remains temporarily for legacy tests/checkers\nKR-2\nCanonical product docs\n/home/editor\n",
    )

    report = build_report(tmp_path)

    assert report.status == "needs_attention"
    assert any("machine/profile-specific" in issue for issue in report.issues)
