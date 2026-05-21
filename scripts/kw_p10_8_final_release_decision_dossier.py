#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-8"
SCHEMA_VERSION = "p10.8.final_release_decision_dossier.v1"
EXPECTED_BASE_AFTER_P10_7 = "6bf239d5f5399923a451d93ddd5f305fc3e51f6a"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md",
    "docs/codex/P10_6_HUMAN_REVIEW_PACKET_EXPORT.md",
    "docs/codex/P10_7A_HUMAN_REVIEW_WORKSHEET_IMPORT_VALIDATOR.md",
    "docs/codex/P10_7_HUMAN_REVIEW_RESULTS_INGEST.md",
    "docs/codex/P10_8_FINAL_RELEASE_DECISION_DOSSIER.md",
    "backend/tests/fixtures/p10/p10_7_human_review_results.json",
    "scripts/kw_p10_7a_human_review_worksheet_import_validator.py",
    "scripts/kw_p10_7_human_review_results_ingest.py",
    "scripts/kw_p10_8_final_release_decision_dossier.py",
    "backend/tests/smoke/test_p10_8_final_release_decision_dossier.py",
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
    errors = [f"missing P10-8 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_7:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_7, head)
            if ancestry is False:
                errors.append(f"expected P10-7 baseline {EXPECTED_BASE_AFTER_P10_7} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-7 ancestry for {EXPECTED_BASE_AFTER_P10_7}..{head}")
    return errors


def run_p10_7_ingest(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_7_human_review_results_ingest.py", "--repo-root", str(repo_root), "--json"]
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


def decision_from_review(p10_7_report: dict[str, Any]) -> tuple[str, str]:
    reject_count = int(p10_7_report.get("reject_count") or 0)
    request_rework_count = int(p10_7_report.get("request_rework_count") or 0)
    blocking_case_ids = p10_7_report.get("blocking_case_ids") if isinstance(p10_7_report.get("blocking_case_ids"), list) else []
    if reject_count:
        return "defer_pending_rejection_resolution", "Human review contains reject decisions; release approval is blocked."
    if request_rework_count or blocking_case_ids:
        return "defer_pending_targeted_rework", "Human review completed, but at least one golden case still requests rework."
    return "ready_for_owner_release_approval_dossier", "All golden cases were approved; owner release approval can be evaluated separately."


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_7_report: dict[str, Any] | None = None
    if not errors:
        p10_7_report, stdout, stderr, returncode = run_p10_7_ingest(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"P10-7 ingest failed during P10-8 decision dossier with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if p10_7_report is None:
            errors.append("P10-8 could not parse P10-7 ingest JSON output")
        elif p10_7_report.get("status") != "ready":
            errors.append(f"P10-7 ingest status is not ready during P10-8: {p10_7_report.get('status')!r}")
        elif p10_7_report.get("human_re_review_completed_by_p10_7") is not True:
            errors.append("P10-8 requires completed P10-7 human review evidence")
    if p10_7_report is None:
        p10_7_report = {}
    release_decision, decision_reason = decision_from_review(p10_7_report)
    approve_count = int(p10_7_report.get("approve_count") or 0)
    request_rework_count = int(p10_7_report.get("request_rework_count") or 0)
    reject_count = int(p10_7_report.get("reject_count") or 0)
    completed_count = int(p10_7_report.get("completed_human_review_decision_count") or 0)
    blocking_case_ids = normalize_list(p10_7_report.get("blocking_case_ids"))
    ready = not errors
    release_approval_supported = bool(ready and release_decision == "ready_for_owner_release_approval_dossier")
    dossier = {
        "mode": "p10-8-final-release-decision-dossier",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_7": EXPECTED_BASE_AFTER_P10_7,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "p10_7_report_digest": digest_payload(p10_7_report) if p10_7_report else None,
        "completed_human_review_decision_count": completed_count,
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "approve_count": approve_count,
        "request_rework_count": request_rework_count,
        "reject_count": reject_count,
        "blocking_case_ids": blocking_case_ids,
        "approved_case_ids": normalize_list(p10_7_report.get("approved_case_ids")),
        "case_min_scores": p10_7_report.get("case_min_scores") if isinstance(p10_7_report.get("case_min_scores"), dict) else {},
        "follow_up_backlog_item_count": int(p10_7_report.get("follow_up_backlog_item_count") or 0),
        "follow_up_backlog": normalize_list(p10_7_report.get("follow_up_backlog")),
        "owner_accepted_ai_assisted_review_used_by_p10_8": bool(p10_7_report.get("review_results_imported_from_owner_accepted_ai_assisted_review") is True),
        "final_release_decision_by_p10_8": release_decision,
        "final_release_decision_reason": decision_reason,
        "release_decision_previous_p10_5": "defer_pending_human_re_review",
        "release_decision_after_p10_7": p10_7_report.get("release_decision_supported_after_p10_7"),
        "release_approval_supported_by_p10_8": release_approval_supported,
        "release_approval_granted_by_p10_8": False,
        "release_can_be_marked_approved_without_owner_waiver": False,
        "approval_state_changed_by_p10_8": False,
        "golden_decks_auto_approved_by_p10_8": False,
        "architecture_case_requires_targeted_rework_or_owner_waiver": "k0_arch_doc_to_architecture_deck" in blocking_case_ids,
        "targeted_rework_case_ids": blocking_case_ids,
        "project_completion_can_use_public_api_dev_gigachat_evidence": True,
        "p10_5a_public_api_dev_evidence_is_real_provider_evidence": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_local_intranet_verification_required_for_p10_8": False,
        "server3_local_intranet_route_verified_by_p10_8": False,
        "server3_local_intranet_operator_readiness_should_be_prepared_separately": True,
        "production_offline_mode_remains_target_deployment_mode": True,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_8": False,
        "api_endpoint_added_by_p10_8": False,
        "db_schema_migration_added_by_p10_8": False,
        "frontend_runtime_changed_by_p10_8": False,
        "dependency_versions_changed_by_p10_8": False,
        "dockerfiles_changed_by_p10_8": False,
        "cloud_llm_added_by_p10_8": False,
        "cloud_vision_added_by_p10_8": False,
        "kimi_level_claimed_by_p10_8": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_8": False,
    }
    if ready and release_decision == "defer_pending_targeted_rework":
        dossier["next_recommended_step"] = "Run a narrow targeted architecture-deck rework or record an explicit owner waiver before any release approval dossier."
    elif ready and release_decision == "ready_for_owner_release_approval_dossier":
        dossier["next_recommended_step"] = "Create a separate owner release approval checkpoint if the operator accepts remaining topology/dependency boundaries."
    else:
        dossier["next_recommended_step"] = "Fix P10-8 dossier prerequisites before changing any release decision."
    dossier["p10_8_dossier_digest"] = digest_payload(dossier)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "p10_8_final_release_decision_dossier.json"
        out.write_text(json.dumps(dossier, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        dossier["p10_8_dossier_file"] = str(out)
    return dossier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-8 final release decision dossier after completed human review.")
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
        print(f"P10-8 final release decision dossier: {report['status']}")
        print(f"final release decision: {report['final_release_decision_by_p10_8']}")
        print(f"completed decisions: {report['completed_human_review_decision_count']}/{report['expected_review_worksheet_count']}")
        print(f"decisions: approve={report['approve_count']} request_rework={report['request_rework_count']} reject={report['reject_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
