#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-11"
SCHEMA_VERSION = "p10.11.final_operator_release_closure.v1"
EXPECTED_BASE_AFTER_P10_10 = "f369412ba284f5f149a81ab42cb25b45b74bfaa4"
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_10_FINAL_RELEASE_APPROVAL_DOSSIER.md",
    "docs/codex/P10_11_FINAL_OPERATOR_RELEASE_CLOSURE.md",
    "scripts/kw_p10_10_final_release_approval_dossier.py",
    "scripts/kw_p10_11_final_operator_release_closure.py",
    "backend/tests/smoke/test_p10_11_final_operator_release_closure.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-11 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_10:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_10, head)
            if ancestry is False:
                errors.append(f"expected P10-10 baseline {EXPECTED_BASE_AFTER_P10_10} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-10 ancestry for {EXPECTED_BASE_AFTER_P10_10}..{head}")
    return errors


def run_p10_10(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_10_final_release_approval_dossier.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_10_report: dict[str, Any] | None = None
    if not errors:
        p10_10_report, stdout, stderr, returncode = run_p10_10(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"P10-10 approval dossier failed during P10-11 closure with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if p10_10_report is None:
            errors.append("P10-11 could not parse P10-10 approval dossier JSON output")
        elif p10_10_report.get("status") != "ready":
            errors.append(f"P10-10 approval dossier is not ready during P10-11: {p10_10_report.get('status')!r}")
        elif p10_10_report.get("release_approval_granted_by_p10_10") is not True:
            errors.append("P10-11 requires P10-10 release approval to be granted")
    if p10_10_report is None:
        p10_10_report = {}
    ready = not errors
    closure = {
        "mode": "p10-11-final-operator-release-closure",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_10": EXPECTED_BASE_AFTER_P10_10,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "p10_10_dossier_digest": digest_payload(p10_10_report) if p10_10_report else None,
        "release_decision_from_p10_10": p10_10_report.get("final_release_decision_by_p10_10"),
        "release_approval_granted_by_p10_10": bool(p10_10_report.get("release_approval_granted_by_p10_10") is True),
        "operator_release_closure_completed_by_p10_11": bool(ready),
        "project_release_status_after_p10_11": "approved_for_operator_handoff" if ready else "not_ready",
        "approved_golden_case_count_after_p10_11": int(p10_10_report.get("approve_count_after_p10_9") or 0),
        "request_rework_count_after_p10_11": int(p10_10_report.get("request_rework_count_after_p10_9") or 0),
        "reject_count_after_p10_11": int(p10_10_report.get("reject_count_after_p10_9") or 0),
        "blocking_case_ids_after_p10_11": p10_10_report.get("blocking_case_ids_after_p10_9") if isinstance(p10_10_report.get("blocking_case_ids_after_p10_9"), list) else [],
        "handoff_profile_1_project_path": "/home/su4ka/workplace/Knowledge_Work_Studio",
        "handoff_profile_2_project_path": "/home/editor/workplace/Knowledge_Work_Studio",
        "operator_logs_must_stay_in_repo_logs": True,
        "downloads_are_handoff_only": True,
        "assistant_must_locally_apply_and_test_future_patches": True,
        "project_completion_can_use_public_api_dev_gigachat_evidence": True,
        "p10_5a_public_api_dev_evidence_is_real_provider_evidence": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_local_intranet_verification_required_for_p10_11": False,
        "server3_local_intranet_route_verified_by_p10_11": False,
        "server3_local_intranet_operator_readiness_should_be_prepared_in_s_track": True,
        "production_offline_mode_remains_target_deployment_mode": True,
        "kimi_slides_class_track_opened_after_release_closure": True,
        "kimi_level_claimed_by_p10_11": False,
        "whole_project_kimi_level_supported": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "npm_audit_fix_force_run_by_p10_11": False,
        "api_endpoint_added_by_p10_11": False,
        "db_schema_migration_added_by_p10_11": False,
        "frontend_runtime_changed_by_p10_11": False,
        "dependency_versions_changed_by_p10_11": False,
        "dockerfiles_changed_by_p10_11": False,
        "cloud_llm_added_by_p10_11": False,
        "cloud_vision_added_by_p10_11": False,
        "network_required_for_p10_11": False,
        "next_recommended_step": "S1 - create Kimi Slides-class capability gap dossier and roadmap without claiming parity.",
    }
    closure["p10_11_closure_digest"] = digest_payload(closure)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "p10_11_final_operator_release_closure.json"
        out.write_text(json.dumps(closure, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        closure["p10_11_closure_file"] = str(out)
    return closure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-11 final operator release closure.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir.resolve() if args.artifacts_dir else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-11 final operator release closure: {report['status']}")
        print(f"project release status: {report['project_release_status_after_p10_11']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
