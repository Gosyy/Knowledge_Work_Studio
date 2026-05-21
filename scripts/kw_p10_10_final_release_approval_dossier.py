#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-10"
SCHEMA_VERSION = "p10.10.final_release_approval_dossier.v1"
EXPECTED_BASE_AFTER_P10_9 = "405a6ea1a418ec1aa5df5648ce0dcba1da2e073d"
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
    "docs/codex/P10_7_HUMAN_REVIEW_RESULTS_INGEST.md",
    "docs/codex/P10_8_FINAL_RELEASE_DECISION_DOSSIER.md",
    "docs/codex/P10_9_TARGETED_ARCHITECTURE_REWORK.md",
    "docs/codex/P10_10_FINAL_RELEASE_APPROVAL_DOSSIER.md",
    "scripts/kw_p10_7_human_review_results_ingest.py",
    "scripts/kw_p10_8_final_release_decision_dossier.py",
    "scripts/kw_p10_9_targeted_architecture_rework.py",
    "scripts/kw_p10_10_final_release_approval_dossier.py",
    "backend/tests/smoke/test_p10_10_final_release_approval_dossier.py",
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
    errors = [f"missing P10-10 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_9:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_9, head)
            if ancestry is False:
                errors.append(f"expected P10-9 baseline {EXPECTED_BASE_AFTER_P10_9} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-9 ancestry for {EXPECTED_BASE_AFTER_P10_9}..{head}")
    return errors


def run_p10_9(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_9_targeted_architecture_rework.py", "--repo-root", str(repo_root), "--json"]
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


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def p10_9_supports_release_approval(report: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if report.get("status") != "ready":
        errors.append(f"P10-9 status must be ready, got {report.get('status')!r}")
    expected = {
        "approve_count_after_p10_9": len(GOLDEN_CASE_IDS),
        "request_rework_count_after_p10_9": 0,
        "reject_count_after_p10_9": 0,
        "release_decision_supported_after_p10_9": "ready_for_final_release_approval_dossier",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            errors.append(f"expected {key}={value!r}, got {report.get(key)!r}")
    if normalize_list(report.get("blocking_case_ids_after_p10_9")):
        errors.append("P10-9 must leave no blocking golden benchmark cases")
    if report.get("architecture_request_rework_resolved_by_p10_9") is not True:
        errors.append("P10-9 must resolve the architecture request-rework case")
    if report.get("release_approval_supported_by_p10_9") is not True:
        errors.append("P10-9 must support final release approval dossier creation")
    if report.get("release_approval_granted_by_p10_9") is not False:
        errors.append("P10-9 must not grant release approval itself")
    if report.get("server3_local_intranet_route_verified_by_p10_9") is not False:
        errors.append("P10-9 must not claim Server 3 local_intranet route verification")
    if report.get("kimi_level_claimed_by_p10_9") is not False:
        errors.append("P10-9 must not claim Kimi-level")
    return not errors, errors


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_9_report: dict[str, Any] | None = None
    if not errors:
        p10_9_report, stdout, stderr, returncode = run_p10_9(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"P10-9 targeted rework failed during P10-10 approval dossier with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if p10_9_report is None:
            errors.append("P10-10 could not parse P10-9 JSON output")
        else:
            ok, support_errors = p10_9_supports_release_approval(p10_9_report)
            if not ok:
                errors.extend(support_errors)
    if p10_9_report is None:
        p10_9_report = {}

    approved_case_ids = list(GOLDEN_CASE_IDS)
    ready = not errors
    release_approved = bool(ready)
    dossier = {
        "mode": "p10-10-final-release-approval-dossier",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_9": EXPECTED_BASE_AFTER_P10_9,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "p10_9_report_digest": digest_payload(p10_9_report) if p10_9_report else None,
        "final_release_decision_by_p10_10": "approved_for_release" if release_approved else "defer_pending_release_approval_prerequisites",
        "release_approval_granted_by_p10_10": release_approved,
        "release_approval_basis": [
            "P9 hardening closed and accepted",
            "P10-1 through P10-9 closed and accepted",
            "completed human review results are present",
            "all five golden benchmark cases are approved after targeted architecture rework",
            "P10-5a public_api_dev GigaChat benchmark provides accepted real provider evidence for project completion path",
            "full runner and Docker smoke are required after this checkpoint before final closure is declared",
        ],
        "completed_human_review_decision_count_after_p10_9": int(p10_9_report.get("approve_count_after_p10_9") or 0),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "approve_count_after_p10_9": int(p10_9_report.get("approve_count_after_p10_9") or 0),
        "request_rework_count_after_p10_9": int(p10_9_report.get("request_rework_count_after_p10_9") or 0),
        "reject_count_after_p10_9": int(p10_9_report.get("reject_count_after_p10_9") or 0),
        "blocking_case_ids_after_p10_9": normalize_list(p10_9_report.get("blocking_case_ids_after_p10_9")),
        "approved_case_ids_after_p10_10": approved_case_ids if release_approved else [],
        "architecture_request_rework_resolved_by_p10_9": bool(p10_9_report.get("architecture_request_rework_resolved_by_p10_9") is True),
        "owner_waiver_used_by_p10_10": False,
        "release_approval_is_waiver_based": False,
        "release_approval_requires_additional_human_review": False,
        "release_approval_requires_targeted_rework": False,
        "project_completion_can_use_public_api_dev_gigachat_evidence": True,
        "p10_5a_public_api_dev_evidence_is_real_provider_evidence": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_local_intranet_verification_required_for_p10_10": False,
        "server3_local_intranet_route_verified_by_p10_10": False,
        "server3_local_intranet_operator_readiness_should_be_prepared_separately": True,
        "production_offline_mode_remains_target_deployment_mode": True,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_10": False,
        "api_endpoint_added_by_p10_10": False,
        "db_schema_migration_added_by_p10_10": False,
        "frontend_runtime_changed_by_p10_10": False,
        "dependency_versions_changed_by_p10_10": False,
        "dockerfiles_changed_by_p10_10": False,
        "cloud_llm_added_by_p10_10": False,
        "cloud_vision_added_by_p10_10": False,
        "kimi_level_claimed_by_p10_10": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_10": False,
    }
    dossier["next_recommended_step"] = (
        "After full runner and Docker smoke pass, close P10 release approval and prepare final project closure/operator readiness checkpoint."
        if ready
        else "Fix P10-10 approval prerequisites before changing release approval state."
    )
    dossier["p10_10_dossier_digest"] = digest_payload(dossier)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "p10_10_final_release_approval_dossier.json"
        out.write_text(json.dumps(dossier, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        dossier["p10_10_dossier_file"] = str(out)
    return dossier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-10 final release approval dossier.")
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
        print(f"P10-10 final release approval dossier: {report['status']}")
        print(f"final release decision: {report['final_release_decision_by_p10_10']}")
        print(f"release approval granted: {report['release_approval_granted_by_p10_10']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
