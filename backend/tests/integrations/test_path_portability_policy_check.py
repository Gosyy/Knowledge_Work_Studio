from __future__ import annotations

from pathlib import Path

from scripts.kw_path_portability_policy_check import build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_path_portability_policy_is_ready_for_current_product_surface() -> None:
    report = build_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["blocking_findings_total"] == 0
    assert report["summary"]["protected_files_scanned"] > 0
    assert report["summary"]["required_policy_files_missing"] == 0


def test_path_portability_policy_blocks_unmarked_absolute_paths_in_product_docs(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "product" / "PRODUCT_VISION.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("This active product doc must not require /home/editor/project.\n", encoding="utf-8")

    report = build_report(tmp_path)

    assert report["status"] == "blocked"
    assert any(finding["pattern"] == "absolute_home_path" for finding in report["blocking_findings"])


def test_path_portability_policy_allows_marked_operator_local_examples(tmp_path: Path) -> None:
    runbook = tmp_path / "docs" / "operators" / "LOCAL_DEVELOPMENT.md"
    runbook.parent.mkdir(parents=True)
    runbook.write_text(
        "# Local development\n\n"
        "Local-only example:\n"
        "cd /home/example/workplace/Knowledge_Work_Studio\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)

    assert report["status"] == "blocked"  # required policy files are absent in this synthetic repo
    assert report["blocking_findings"] == []
    assert any(
        finding["allowed_reason"] == "explicitly marked local-only operator example"
        for finding in report["allowed_findings"]
    )


def test_path_portability_policy_detects_raw_git_sha_in_product_tests(tmp_path: Path) -> None:
    test_file = tmp_path / "backend" / "tests" / "workflows" / "test_example_workflow.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_bad_commit_pin():\n"
        "    assert '0123456789abcdef0123456789abcdef01234567'\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path)

    assert report["status"] == "blocked"
    assert any(finding["pattern"] == "raw_git_sha" for finding in report["blocking_findings"])
