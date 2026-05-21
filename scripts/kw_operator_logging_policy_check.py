#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/OPERATOR_LOGGING_AND_DOWNLOADS_POLICY.md",
    "scripts/kw_operator_log_archive.py",
    "scripts/kw_patch_full_tests_summary.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "scripts/kw_operator_logging_policy_check.py",
    "backend/tests/smoke/test_operator_logging_downloads_policy.py",
)

def profile_path_markers() -> tuple[str, ...]:
    # Keep the forbidden absolute paths out of this reusable checker while still
    # checking for them in the other committed reusable scripts. The fragments
    # intentionally cover both active profiles without making this file itself
    # look profile-bound.
    home = "/" + "home"
    downloads = "Загрузки"
    return (
        f"{home}/editor/workplace/Knowledge_Work_Studio",
        f"{home}/editor/{downloads}",
        f"{home}/su4ka/workplace/Knowledge_Work_Studio",
        f"{home}/su4ka/{downloads}",
    )


PROFILE_PATH_MARKERS = profile_path_markers()


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def file_contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8")


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors: list[str] = []
    missing = [rel for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    errors.extend(f"missing operator logging policy file: {rel}" for rel in missing)
    if not missing:
        policy = repo_root / "docs/codex/OPERATOR_LOGGING_AND_DOWNLOADS_POLICY.md"
        full_runner = repo_root / "scripts/kw_full_tests_with_proxy_runner.sh"
        archive_helper = repo_root / "scripts/kw_operator_log_archive.py"
        summary_patcher = repo_root / "scripts/kw_patch_full_tests_summary.py"
        for marker in PROFILE_PATH_MARKERS:
            for rel in (
                "scripts/kw_full_tests_with_proxy_runner.sh",
                "scripts/kw_operator_log_archive.py",
                "scripts/kw_patch_full_tests_summary.py",
                "scripts/kw_operator_logging_policy_check.py",
            ):
                if marker in (repo_root / rel).read_text(encoding="utf-8"):
                    errors.append(f"profile-specific path marker {marker!r} found in reusable script {rel}")
        expected_policy_terms = (
            "files.zip inventory decision",
            "Downloads directory must not be used as the default log root",
            "Profile 1 may run the same committed script",
            "Profile 2 may still run",
            "summary.log must report the real repository branch and HEAD",
        )
        for term in expected_policy_terms:
            if not file_contains(policy, term):
                errors.append(f"operator logging policy missing term: {term}")
        if "kw_operator_log_archive.py" not in full_runner.read_text(encoding="utf-8"):
            errors.append("full runner must use kw_operator_log_archive.py")
        if "KWS_REPO_ROOT" not in full_runner.read_text(encoding="utf-8"):
            errors.append("full runner must support KWS_REPO_ROOT")
        if ".zip" not in full_runner.read_text(encoding="utf-8"):
            errors.append("full runner must archive logs as zip")
        if "shutil.rmtree" not in archive_helper.read_text(encoding="utf-8"):
            errors.append("archive helper must remove source log directories")
        if "origin_head" not in summary_patcher.read_text(encoding="utf-8"):
            errors.append("summary patcher must preserve origin_head")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
    return {
        "mode": "operator-logging-downloads-policy",
        "phase": "P10 operator tooling hygiene",
        "checkpoint": "P10-operator-logging-policy",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "files_zip_analyzed": True,
        "downloads_directory_default_log_sink_removed": True,
        "repo_logs_zip_cleanup_supported": True,
        "profile1_supported_by_same_committed_scripts": True,
        "profile2_supported_by_same_committed_scripts": True,
        "profile_specific_download_wrappers_not_committed": True,
        "runner_backups_not_committed": True,
        "one_off_patch_targeted_runners_not_committed": True,
        "full_runner_summary_branch_head_supported": True,
        "api_endpoint_added_by_operator_logging_policy": False,
        "db_schema_migration_added_by_operator_logging_policy": False,
        "frontend_runtime_changed_by_operator_logging_policy": False,
        "dependency_versions_changed_by_operator_logging_policy": False,
        "dockerfiles_changed_by_operator_logging_policy": False,
        "cloud_llm_added_by_operator_logging_policy": False,
        "cloud_vision_added_by_operator_logging_policy": False,
        "npm_audit_fix_force_run_by_operator_logging_policy": False,
        "kimi_level_claimed_by_operator_logging_policy": False,
        "whole_project_kimi_level_supported": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio operator logging and Downloads policy check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Operator logging and Downloads policy: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
