from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_operator_logging_policy_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_operator_logging_policy_checker_reports_ready() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["files_zip_analyzed"] is True
    assert payload["downloads_directory_default_log_sink_removed"] is True
    assert payload["repo_logs_zip_cleanup_supported"] is True
    assert payload["profile1_supported_by_same_committed_scripts"] is True
    assert payload["profile2_supported_by_same_committed_scripts"] is True
    assert payload["profile_specific_download_wrappers_not_committed"] is True
    assert payload["runner_backups_not_committed"] is True
    assert payload["one_off_patch_targeted_runners_not_committed"] is True
    assert payload["dependency_versions_changed_by_operator_logging_policy"] is False
    assert payload["npm_audit_fix_force_run_by_operator_logging_policy"] is False
    assert payload["kimi_level_claimed_by_operator_logging_policy"] is False


def test_reusable_operator_scripts_are_profile_portable() -> None:
    root = repo_root()
    reusable_scripts = (
        root / "scripts/kw_full_tests_with_proxy_runner.sh",
        root / "scripts/kw_operator_log_archive.py",
        root / "scripts/kw_patch_full_tests_summary.py",
        root / "scripts/kw_operator_logging_policy_check.py",
    )
    forbidden = (
        "/home/editor/workplace/Knowledge_Work_Studio",
        "/home/editor/Загрузки",
        "/home/su4ka/workplace/Knowledge_Work_Studio",
        "/home/su4ka/Загрузки",
    )
    for script in reusable_scripts:
        text = script.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"{marker!r} found in {script}"
    full_runner = (root / "scripts/kw_full_tests_with_proxy_runner.sh").read_text(encoding="utf-8")
    assert "KWS_REPO_ROOT" in full_runner
    assert "kw_operator_log_archive.py" in full_runner
    assert ".zip" in full_runner


def test_policy_documents_files_zip_classification() -> None:
    text = (repo_root() / "docs/codex/OPERATOR_LOGGING_AND_DOWNLOADS_POLICY.md").read_text(encoding="utf-8")
    assert "patch_full_tests_summary_branch_profile2_v3.py" in text
    assert "run_kws_full_tests_with_proxy.sh.orig-summary-branch" in text
    assert "kws_runner_backups/*" in text
    assert "run_p10_2_post_p9_artifact_pack_targeted_profile2.sh" in text
    assert "Do not commit" in text
    assert "Refactor and commit" in text
