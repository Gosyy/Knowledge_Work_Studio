#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-7"
SCHEMA_VERSION = "p10.7.human_review_results_ingest.v1"
EXPECTED_BASE_AFTER_P10_7A = "0084a9fd9e0b45480c4881097b291a8855517a92"
DEFAULT_REVIEW_RESULTS = Path("backend/tests/fixtures/p10/p10_7_human_review_results.json")
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
    "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md",
    "docs/codex/P10_6_HUMAN_REVIEW_PACKET_EXPORT.md",
    "docs/codex/P10_7A_HUMAN_REVIEW_WORKSHEET_IMPORT_VALIDATOR.md",
    "docs/codex/P10_7_HUMAN_REVIEW_RESULTS_INGEST.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "backend/tests/fixtures/p10/p10_7_human_review_results.json",
    "scripts/kw_p10_7a_human_review_worksheet_import_validator.py",
    "scripts/kw_p10_7_human_review_results_ingest.py",
    "backend/tests/smoke/test_p10_7_human_review_results_ingest.py",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-7 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_7A:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_7A, head)
            if ancestry is False:
                errors.append(f"expected P10-7a baseline {EXPECTED_BASE_AFTER_P10_7A} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-7a ancestry for {EXPECTED_BASE_AFTER_P10_7A}..{head}")
    return errors


def run_p10_7a_validator(repo_root: Path, review_results: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_7a_human_review_worksheet_import_validator.py", "--repo-root", str(repo_root), "--review-results", str(review_results), "--json"]
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


def extract_worksheets(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("review_worksheets"), list):
        return [item for item in payload["review_worksheets"] if isinstance(item, dict)]
    return []


def summarize_review_results(review_payload: dict[str, Any], validator_payload: dict[str, Any]) -> dict[str, Any]:
    worksheets = extract_worksheets(review_payload)
    by_case = {str(item.get("case_id") or ""): item for item in worksheets}
    decision_counts = {"approve": 0, "request_rework": 0, "reject": 0}
    blocking_case_ids: list[str] = []
    approved_case_ids: list[str] = []
    follow_up_backlog: list[dict[str, Any]] = []
    case_min_scores: dict[str, int] = {}
    for case_id in GOLDEN_CASE_IDS:
        worksheet = by_case.get(case_id, {})
        decision = str(worksheet.get("decision") or "")
        if decision in decision_counts:
            decision_counts[decision] += 1
        if decision == "approve":
            approved_case_ids.append(case_id)
        else:
            blocking_case_ids.append(case_id)
        scores = worksheet.get("scores") if isinstance(worksheet.get("scores"), dict) else {}
        numeric_scores = [value for value in scores.values() if isinstance(value, int) and not isinstance(value, bool)]
        if numeric_scores:
            case_min_scores[case_id] = min(numeric_scores)
            if min(numeric_scores) <= 2 and case_id not in blocking_case_ids:
                blocking_case_ids.append(case_id)
        backlog = worksheet.get("follow_up_backlog", []) if isinstance(worksheet.get("follow_up_backlog"), list) else []
        for item in backlog:
            if isinstance(item, dict):
                merged = {"case_id": case_id, **item}
            else:
                merged = {"case_id": case_id, "summary": str(item)}
            follow_up_backlog.append(merged)
    all_approved = decision_counts["approve"] == len(GOLDEN_CASE_IDS)
    return {
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "completed_human_review_decision_count": int(validator_payload.get("completed_human_review_decision_count") or 0),
        "pending_human_review_decision_count": int(validator_payload.get("pending_human_review_decision_count") or 0),
        "approve_count": decision_counts["approve"],
        "request_rework_count": decision_counts["request_rework"],
        "reject_count": decision_counts["reject"],
        "approved_case_ids": approved_case_ids,
        "blocking_case_ids": sorted(set(blocking_case_ids)),
        "case_min_scores": case_min_scores,
        "follow_up_backlog_item_count": len(follow_up_backlog),
        "follow_up_backlog": follow_up_backlog,
        "all_cases_approved_by_human_review": all_approved,
        "release_can_be_approved_from_human_review": False,
        "release_decision_supported_after_p10_7": "defer_pending_review_rework" if not all_approved else "ready_for_final_decision_dossier",
    }


def build_report(repo_root: Path, review_results: Path | None, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    review_results_path = (review_results or (repo_root / DEFAULT_REVIEW_RESULTS)).resolve()
    validator_payload: dict[str, Any] | None = None
    review_payload: dict[str, Any] = {}
    summary: dict[str, Any] = {
        "review_worksheet_count": 0,
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "completed_human_review_decision_count": 0,
        "pending_human_review_decision_count": len(GOLDEN_CASE_IDS),
        "approve_count": 0,
        "request_rework_count": 0,
        "reject_count": 0,
        "approved_case_ids": [],
        "blocking_case_ids": [],
        "case_min_scores": {},
        "follow_up_backlog_item_count": 0,
        "follow_up_backlog": [],
        "all_cases_approved_by_human_review": False,
        "release_can_be_approved_from_human_review": False,
        "release_decision_supported_after_p10_7": "defer_pending_human_re_review",
    }
    if not review_results_path.exists():
        errors.append(f"P10-7 review results file does not exist: {review_results_path}")
    if not errors:
        try:
            loaded = load_json(review_results_path)
            if isinstance(loaded, dict):
                review_payload = loaded
            else:
                errors.append("P10-7 review results payload must be a JSON object")
        except Exception as exc:
            errors.append(f"could not load P10-7 review results JSON: {exc}")
    if not errors:
        validator_payload, stdout, stderr, returncode = run_p10_7a_validator(repo_root, review_results_path, require_ready)
        if returncode != 0:
            errors.append(f"P10-7a validator rejected P10-7 review results with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if validator_payload is None:
            errors.append("P10-7 could not parse P10-7a validator JSON output")
        elif validator_payload.get("status") != "ready" or validator_payload.get("review_results_importable_by_p10_7a") is not True:
            errors.append(f"P10-7a validator did not mark review results importable: status={validator_payload.get('status')!r}")
        elif validator_payload.get("human_re_review_completed") is not True:
            errors.append("P10-7 requires completed human review results for all five worksheets")
    if not errors and validator_payload is not None:
        summary = summarize_review_results(review_payload, validator_payload)
        if summary["completed_human_review_decision_count"] != len(GOLDEN_CASE_IDS):
            errors.append("P10-7 requires all five human review decisions to be completed")
        if summary["request_rework_count"] or summary["reject_count"]:
            summary["release_can_be_approved_from_human_review"] = False
            summary["release_decision_supported_after_p10_7"] = "defer_pending_review_rework"
    ready = not errors
    report = {
        "mode": "p10-7-human-review-results-ingest",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_7a": EXPECTED_BASE_AFTER_P10_7A,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "review_results_file": str(review_results_path),
        "review_results_digest": digest_payload(review_payload) if review_payload else None,
        "validator_status": validator_payload.get("status") if isinstance(validator_payload, dict) else None,
        "validator_report_digest": digest_payload(validator_payload) if isinstance(validator_payload, dict) else None,
        "p10_7_completed_human_review_results_ingested": bool(ready),
        "human_re_review_completed_by_p10_7": bool(ready and summary["completed_human_review_decision_count"] == len(GOLDEN_CASE_IDS)),
        "review_results_imported_from_owner_accepted_ai_assisted_review": bool(review_payload.get("owner_acceptance_recorded") is True),
        "release_decision_remains": "defer_pending_human_re_review",
        "release_decision_supported_after_p10_7": summary["release_decision_supported_after_p10_7"],
        "release_approval_granted_by_p10_7": False,
        "approval_state_changed_by_p10_7": False,
        "golden_decks_auto_approved_by_p10_7": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_offline_intranet_route_verified_by_p10_7": False,
        "project_completion_can_use_public_api_dev_gigachat_evidence": True,
        "server3_local_intranet_preparation_remaining_track": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_7": False,
        "api_endpoint_added_by_p10_7": False,
        "db_schema_migration_added_by_p10_7": False,
        "frontend_runtime_changed_by_p10_7": False,
        "dependency_versions_changed_by_p10_7": False,
        "dockerfiles_changed_by_p10_7": False,
        "cloud_llm_added_by_p10_7": False,
        "cloud_vision_added_by_p10_7": False,
        "kimi_level_claimed_by_p10_7": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_7": False,
        **summary,
    }
    report["p10_7_report_digest"] = digest_payload(report)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifacts_dir / "p10_7_human_review_results_ingest_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["p10_7_report_file"] = str(report_path)
    if ready and summary["request_rework_count"]:
        report["next_recommended_step"] = "P10-8 final decision dossier should keep release deferred and scope a targeted rework/waiver decision for the architecture deck."
    elif ready:
        report["next_recommended_step"] = "P10-8 final decision dossier can evaluate release approval from completed human review evidence."
    else:
        report["next_recommended_step"] = "Fix P10-7 review results and rerun ingest before any final decision dossier."
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-7 completed human review results ingest.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--review-results", type=Path, default=None)
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.review_results.resolve() if args.review_results else None, args.artifacts_dir.resolve() if args.artifacts_dir else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-7 human review results ingest: {report['status']}")
        print(f"completed decisions: {report['completed_human_review_decision_count']}/{report['expected_review_worksheet_count']}")
        print(f"decisions: approve={report['approve_count']} request_rework={report['request_rework_count']} reject={report['reject_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
