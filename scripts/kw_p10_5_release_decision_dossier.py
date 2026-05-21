#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-5"
SCHEMA_VERSION = "p10.5.release_decision_dossier.v1"
EXPECTED_BASE_AFTER_P10_5A = "157776bc14cb759c4a8b2bd3453d41f6c02dde52"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_4_POST_P9_HUMAN_RE_REVIEW_CAPTURE.md",
    "docs/codex/P10_5A_GIGACHAT_API_GOLDEN_BENCHMARK.md",
    "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_p10_4_post_p9_human_re_review.py",
    "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py",
    "scripts/kw_p10_5_release_decision_dossier.py",
    "backend/tests/smoke/test_p10_5_release_decision_dossier.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-5 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_5A:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_5A, head)
            if ancestry is False:
                errors.append(f"expected P10-5a baseline {EXPECTED_BASE_AFTER_P10_5A} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-5a ancestry for {EXPECTED_BASE_AFTER_P10_5A}..{head}")
    return errors


def run_json_script(repo_root: Path, *command: str) -> tuple[dict[str, Any] | None, str, str, int]:
    result = subprocess.run((sys.executable, *command), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            payload = parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def run_p10_4_capture(repo_root: Path, artifacts_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    return run_json_script(
        repo_root,
        "scripts/kw_p10_4_post_p9_human_re_review.py",
        "--repo-root",
        str(repo_root),
        "--artifacts-dir",
        str(artifacts_root),
        "--require-ready",
        "--json",
    )


def run_p10_5a_static(repo_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    return run_json_script(
        repo_root,
        "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py",
        "--repo-root",
        str(repo_root),
        "--require-ready",
        "--json",
    )


def review_completion_state(p10_4_payload: dict[str, Any]) -> dict[str, Any]:
    worksheets = p10_4_payload.get("review_worksheets", []) if isinstance(p10_4_payload.get("review_worksheets"), list) else []
    decisions = [item.get("decision") for item in worksheets if isinstance(item, dict)]
    pending = sum(1 for decision in decisions if decision in (None, "", "pending_human_review"))
    approve = sum(1 for decision in decisions if decision == "approve")
    request_rework = sum(1 for decision in decisions if decision == "request_rework")
    reject = sum(1 for decision in decisions if decision == "reject")
    completed = len(decisions) - pending
    return {
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "completed_human_review_decision_count": completed,
        "pending_human_review_decision_count": pending,
        "approve_count": approve,
        "request_rework_count": request_rework,
        "reject_count": reject,
        "human_re_review_completed": completed == len(GOLDEN_CASE_IDS) and len(worksheets) == len(GOLDEN_CASE_IDS),
        "all_review_decisions_pending": pending == len(GOLDEN_CASE_IDS) and len(worksheets) == len(GOLDEN_CASE_IDS),
    }


def build_decision_dossier(repo_root: Path, p10_4_payload: dict[str, Any], p10_5a_payload: dict[str, Any]) -> dict[str, Any]:
    state = review_completion_state(p10_4_payload)
    human_review_completed = bool(state["human_re_review_completed"])
    if human_review_completed and state["approve_count"] == len(GOLDEN_CASE_IDS):
        release_decision = "approve_after_human_re_review"
        release_approval_granted = True
    elif human_review_completed and state["reject_count"] > 0:
        release_decision = "reject_after_human_re_review"
        release_approval_granted = False
    elif human_review_completed:
        release_decision = "request_rework_after_human_re_review"
        release_approval_granted = False
    else:
        release_decision = "defer_pending_human_re_review"
        release_approval_granted = False
    blockers = []
    if not human_review_completed:
        blockers.append("post-P9 human re-review is not completed; P10-4 worksheets remain pending")
    if p10_5a_payload.get("production_route_verified_by_p10_5a") is not True:
        blockers.append("P10-5a used public_api_dev evidence and does not verify offline/intranet Server 3 route")
    blockers.append("known npm audit/deprecated warnings remain on separate controlled dependency/security track")
    dossier = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint": CHECKPOINT,
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_5a": EXPECTED_BASE_AFTER_P10_5A,
        "p10_4_capture_digest": digest_payload(p10_4_payload),
        "p10_5a_static_contract_digest": digest_payload(p10_5a_payload),
        "p10_5_release_decision_dossier_supported": True,
        "release_decision": release_decision,
        "release_approval_granted_by_p10_5": release_approval_granted,
        "release_decision_is_deferred": release_decision == "defer_pending_human_re_review",
        "decision_blockers": blockers,
        "golden_case_count": len(GOLDEN_CASE_IDS),
        **state,
        "p10_5a_gigachat_api_evidence_included": True,
        "p10_5a_gigachat_provider_route": "public_api_dev",
        "p10_5a_public_api_dev_is_not_server3_offline_proof": True,
        "server3_offline_intranet_route_verified_by_p10_5": False,
        "post_p9_human_re_review_required_before_release_approval": True,
        "approval_state_changed_by_p10_5": False,
        "golden_decks_auto_approved_by_p10_5": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_5": False,
        "api_endpoint_added_by_p10_5": False,
        "db_schema_migration_added_by_p10_5": False,
        "frontend_runtime_changed_by_p10_5": False,
        "dependency_versions_changed_by_p10_5": False,
        "dockerfiles_changed_by_p10_5": False,
        "cloud_llm_added_by_p10_5": False,
        "cloud_vision_added_by_p10_5": False,
        "kimi_level_claimed_by_p10_5": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_5_static_dossier": False,
        "next_recommended_step": "Complete the actual post-P9 human re-review worksheets, then create a final release approval/rework/reject dossier from those completed decisions.",
    }
    dossier["release_decision_dossier_digest"] = digest_payload(dossier)
    return dossier


def build_report_with_artifacts(repo_root: Path, artifacts_root: Path, persist_artifacts: bool, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_4_payload: dict[str, Any] | None = None
    p10_5a_payload: dict[str, Any] | None = None
    dossier: dict[str, Any] = {}
    if not errors:
        artifacts_root.mkdir(parents=True, exist_ok=True)
        p10_4_payload, stdout4, stderr4, returncode4 = run_p10_4_capture(repo_root, artifacts_root / "p10_4_capture")
        if returncode4 != 0:
            errors.append(f"P10-4 capture failed during P10-5 decision dossier with exit code {returncode4}: {stderr4.strip() or stdout4.strip()[:500]}")
        if p10_4_payload is None:
            errors.append("P10-5 could not parse P10-4 capture JSON output")
        elif p10_4_payload.get("status") != "ready":
            errors.append(f"P10-4 capture status is not ready during P10-5 dossier: {p10_4_payload.get('status')}")
        p10_5a_payload, stdout5a, stderr5a, returncode5a = run_p10_5a_static(repo_root)
        if returncode5a != 0:
            errors.append(f"P10-5a static contract failed during P10-5 decision dossier with exit code {returncode5a}: {stderr5a.strip() or stdout5a.strip()[:500]}")
        if p10_5a_payload is None:
            errors.append("P10-5 could not parse P10-5a static JSON output")
        elif p10_5a_payload.get("status") != "ready":
            errors.append(f"P10-5a static contract status is not ready during P10-5 dossier: {p10_5a_payload.get('status')}")
        if p10_4_payload is not None and p10_5a_payload is not None:
            dossier = build_decision_dossier(repo_root, p10_4_payload, p10_5a_payload)
            dossier_path = artifacts_root / "p10_5_release_decision_dossier.json"
            dossier_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    ready = not errors and bool(dossier)
    return {
        "mode": "p10-5-release-decision-dossier",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_5a": EXPECTED_BASE_AFTER_P10_5A,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "artifacts_root": str(artifacts_root),
        "release_dossier_persisted": persist_artifacts,
        "release_decision_dossier": dossier,
        "release_decision_dossier_file": str(artifacts_root / "p10_5_release_decision_dossier.json") if dossier else None,
        **{key: dossier.get(key) for key in (
            "release_decision",
            "release_approval_granted_by_p10_5",
            "release_decision_is_deferred",
            "completed_human_review_decision_count",
            "pending_human_review_decision_count",
            "human_re_review_completed",
            "p10_5a_public_api_dev_is_not_server3_offline_proof",
            "server3_offline_intranet_route_verified_by_p10_5",
            "approval_state_changed_by_p10_5",
            "golden_decks_auto_approved_by_p10_5",
            "kimi_level_claimed_by_p10_5",
            "whole_project_kimi_level_supported",
        )},
    }


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    if artifacts_dir is not None:
        return build_report_with_artifacts(repo_root, artifacts_dir.resolve(), True, require_ready)
    with tempfile.TemporaryDirectory(prefix="kw_p10_5_release_decision_") as tmp:
        return build_report_with_artifacts(repo_root, Path(tmp), False, require_ready)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-5 release decision dossier.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-5 release decision dossier: {report['status']}")
        print(f"release decision: {report.get('release_decision')}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
