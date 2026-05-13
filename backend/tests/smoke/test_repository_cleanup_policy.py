from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


def _write_synthetic_audit(audit_dir: Path) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": {
            "docs_total": 4,
            "tests_total": 3,
            "scripts_total": 3,
            "path_portability_findings_total": 3,
        },
        "repo_root": str(audit_dir.parent),
        "docs_inventory": [
            {
                "kind": "doc",
                "path": "docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md",
                "reason": "stage-specific documentation",
                "recommendation": "archive_or_delete",
            },
            {
                "kind": "doc",
                "path": "docs/workflows/SLIDES_WORKFLOW.md",
                "reason": "target product workflow documentation",
                "recommendation": "keep_or_rewrite_as_product_doc",
            },
            {
                "kind": "doc",
                "path": "docs/deployment-packaging.md",
                "reason": "documentation outside the target product documentation structure",
                "recommendation": "review",
            },
        ],
        "tests_inventory": [
            {
                "kind": "test",
                "path": "backend/tests/smoke/test_s13j_executive_memo_salvage.py",
                "reason": "stage-specific smoke test",
                "recommendation": "rewrite_or_delete",
            },
            {
                "kind": "test",
                "path": "backend/tests/api/test_artifact_download.py",
                "reason": "product API test",
                "recommendation": "keep_or_consolidate",
            },
        ],
        "scripts_inventory": [
            {
                "kind": "script",
                "path": "scripts/kw_kq1b_exec_memo_pptx_generate.py",
                "reason": "stage-specific operator script",
                "recommendation": "archive_or_replace_with_product_tool",
            },
            {
                "kind": "script",
                "path": "scripts/kw_operator_log_archive.py",
                "reason": "operator/product script",
                "recommendation": "keep_or_review",
            },
        ],
        "portability_findings": [
            {
                "path": "docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md",
                "line": 10,
                "pattern": "absolute_home_path",
                "snippet": "cd /home/editor/workplace/Knowledge_Work_Studio",
            },
            {
                "path": "docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md",
                "line": 11,
                "pattern": "profile_specific_label",
                "snippet": "Profile 2",
            },
            {
                "path": "scripts/kw_example.py",
                "line": 5,
                "pattern": "raw_git_sha",
                "snippet": "abcdef0123456789abcdef0123456789abcdef01",
            },
        ],
        "workflow_coverage": [
            {
                "workflow": "xlsx",
                "status": "incomplete",
                "missing_docs": ["docs/workflows/XLSX_WORKFLOW.md", "docs/quality/XLSX_VALIDATION.md"],
                "present_docs": [],
                "matching_files": ["backend/app/services/xlsx_service/__init__.py"],
            }
        ],
    }
    (audit_dir / "cleanup_inventory.json").write_text(json.dumps(payload), encoding="utf-8")


def test_cleanup_policy_generates_product_rewrite_map_from_audit_dir(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    audit_dir = tmp_path / "audit"
    output_dir = tmp_path / "policy"
    zip_out = tmp_path / "policy.zip"
    _write_synthetic_audit(audit_dir)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/kw_repo_cleanup_policy.py"),
            "--audit-dir",
            str(audit_dir),
            "--output-dir",
            str(output_dir),
            "--zip-out",
            str(zip_out),
            "--json",
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ready"
    assert summary["workflow_count"] == 6
    assert summary["path_neutralization_count"] == 2
    assert zip_out.exists()

    policy = json.loads((output_dir / "cleanup_policy.json").read_text(encoding="utf-8"))
    decisions = {(item["path"], item["action"]) for item in policy["decisions"]}
    assert ("docs/codex/S13J_EXECUTIVE_MEMO_SALVAGE.md", "archive") in decisions
    assert ("backend/tests/smoke/test_s13j_executive_memo_salvage.py", "rewrite") in decisions
    assert ("scripts/kw_kq1b_exec_memo_pptx_generate.py", "rewrite") in decisions
    assert any(item["workflow"] == "xlsx" for item in policy["workflow_rewrite_plan"])
    assert any(item["from"] == "scripts/kw_kq1b_exec_memo_pptx_generate.py" for item in policy["rename_plan"])

    with zipfile.ZipFile(zip_out) as zf:
        assert "cleanup_policy.json" in zf.namelist()
        assert "cleanup_policy.md" in zf.namelist()


def test_cleanup_policy_accepts_audit_zip(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    audit_dir = tmp_path / "audit"
    output_dir = tmp_path / "policy"
    audit_zip = tmp_path / "audit.zip"
    _write_synthetic_audit(audit_dir)
    with zipfile.ZipFile(audit_zip, "w") as zf:
        zf.write(audit_dir / "cleanup_inventory.json", "cleanup_inventory.json")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/kw_repo_cleanup_policy.py"),
            "--audit-zip",
            str(audit_zip),
            "--output-dir",
            str(output_dir),
            "--json",
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    policy = json.loads((output_dir / "cleanup_policy.json").read_text(encoding="utf-8"))
    assert policy["product_identity"]["mandatory_workflows"] == [
        "docx",
        "pdf",
        "xlsx",
        "slides",
        "python_analysis",
        "browser_evidence",
    ]
