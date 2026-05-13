from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.kw_archive_obsolete_stage_docs import archive_obsolete_stage_docs
from scripts.kw_archived_stage_docs_check import check_archived_stage_docs


def _write_policy_zip(path: Path) -> None:
    payload = {
        "schema_version": "1.0",
        "decisions": [
            {
                "kind": "doc",
                "action": "archive",
                "path": "docs/codex/S13_EXAMPLE.md",
                "priority": "high",
                "reason": "stage-specific development history",
            },
            {
                "kind": "doc",
                "action": "archive",
                "path": "docs/deployment/migrations.md",
                "priority": "medium",
                "reason": "legacy migration documentation",
            },
            {
                "kind": "doc",
                "action": "keep",
                "path": "docs/product/PRODUCT_VISION.md",
                "priority": "high",
                "reason": "active product documentation",
            },
            {
                "kind": "test",
                "action": "rewrite",
                "path": "backend/tests/smoke/test_s13_example.py",
                "priority": "medium",
                "reason": "not a documentation file",
            },
        ],
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("cleanup_policy.json", json.dumps(payload, indent=2))


def test_archive_obsolete_stage_docs_moves_only_archive_doc_decisions(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/codex").mkdir(parents=True)
    (repo / "docs/deployment").mkdir(parents=True)
    (repo / "docs/product").mkdir(parents=True)
    (repo / "backend/tests/smoke").mkdir(parents=True)

    (repo / "docs/codex/S13_EXAMPLE.md").write_text("stage doc\n", encoding="utf-8")
    (repo / "docs/deployment/migrations.md").write_text("legacy doc\n", encoding="utf-8")
    (repo / "docs/product/PRODUCT_VISION.md").write_text("product doc\n", encoding="utf-8")
    (repo / "backend/tests/smoke/test_s13_example.py").write_text("def test_x(): pass\n", encoding="utf-8")

    policy_zip = tmp_path / "policy.zip"
    _write_policy_zip(policy_zip)

    report = archive_obsolete_stage_docs(
        repo_root=repo,
        policy_path=policy_zip,
        output_dir=tmp_path / "report",
        execute=True,
        allow_missing=False,
    )

    assert report["summary"]["moved_count"] == 2
    assert not (repo / "docs/codex/S13_EXAMPLE.md").exists()
    assert not (repo / "docs/deployment/migrations.md").exists()
    assert (repo / "docs/archive/development-history/codex/S13_EXAMPLE.md").read_text(encoding="utf-8") == "stage doc\n"
    assert (repo / "docs/archive/development-history/deployment/migrations.md").read_text(encoding="utf-8") == "legacy doc\n"
    assert (repo / "docs/product/PRODUCT_VISION.md").exists()
    assert (repo / "backend/tests/smoke/test_s13_example.py").exists()
    assert (tmp_path / "report/obsolete_stage_docs_archive_manifest.json").exists()
    assert (tmp_path / "report/obsolete_stage_docs_archive_manifest.md").exists()

    check = check_archived_stage_docs(
        repo_root=repo,
        policy_path=policy_zip,
        output_dir=tmp_path / "check",
        require_ready=True,
    )
    assert check["status"] == "ready"
    assert check["summary"]["active_legacy_doc_count"] == 0


def test_archive_obsolete_stage_docs_dry_run_does_not_move(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/codex").mkdir(parents=True)
    (repo / "docs/codex/KQ_EXAMPLE.md").write_text("stage doc\n", encoding="utf-8")

    policy_payload = {
        "schema_version": "1.0",
        "decisions": [
            {
                "kind": "doc",
                "action": "archive",
                "path": "docs/codex/KQ_EXAMPLE.md",
                "priority": "high",
                "reason": "stage-specific development history",
            }
        ],
    }
    policy_json = tmp_path / "cleanup_policy.json"
    policy_json.write_text(json.dumps(policy_payload), encoding="utf-8")

    report = archive_obsolete_stage_docs(
        repo_root=repo,
        policy_path=policy_json,
        output_dir=tmp_path / "dry-run-report",
        execute=False,
        allow_missing=False,
    )

    assert report["summary"]["planned_count"] == 1
    assert report["summary"]["moved_count"] == 0
    assert (repo / "docs/codex/KQ_EXAMPLE.md").exists()
    assert not (repo / "docs/archive/development-history/codex/KQ_EXAMPLE.md").exists()
