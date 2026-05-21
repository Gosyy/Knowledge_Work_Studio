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

CHECKPOINT = "P10-4"
SCHEMA_VERSION = "p10.4.post_p9_human_re_review_capture.v1"
EXPECTED_BASE_AFTER_P10_3 = "c854830ae885ffdde80da6a3de6c0f7466433bd2"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_3_POST_P9_ARTIFACT_COMPARISON.md",
    "docs/codex/P10_4_POST_P9_HUMAN_RE_REVIEW_CAPTURE.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_p10_3_post_p9_artifact_comparison.py",
    "scripts/kw_p10_4_post_p9_human_re_review.py",
    "backend/tests/smoke/test_p10_4_post_p9_human_re_review.py",
)
ALLOWED_DECISIONS = ("approve", "request_rework", "reject")
REQUIRED_REVIEW_FIELDS = (
    "reviewer_id",
    "reviewed_at",
    "decision",
    "scores",
    "slide_level_findings",
    "follow_up_backlog",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-4 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_3:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_3, head)
            if ancestry is False:
                errors.append(f"expected P10-3 baseline {EXPECTED_BASE_AFTER_P10_3} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-3 ancestry for {EXPECTED_BASE_AFTER_P10_3}..{head}")
    return errors


def run_p10_3_comparison(repo_root: Path, artifacts_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    command = (
        sys.executable,
        "scripts/kw_p10_3_post_p9_artifact_comparison.py",
        "--repo-root",
        str(repo_root),
        "--artifacts-dir",
        str(artifacts_root),
        "--require-ready",
        "--json",
    )
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def load_review_dimensions(repo_root: Path) -> tuple[dict[str, Any], ...]:
    payload = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
    dimensions = payload.get("review_dimensions", []) if isinstance(payload, dict) else []
    return tuple(dim for dim in dimensions if isinstance(dim, dict))


def build_review_worksheets(repo_root: Path, comparison_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    cards = comparison_payload.get("case_comparison_cards", []) if isinstance(comparison_payload.get("case_comparison_cards"), list) else []
    by_case = {str(card.get("case_id") or ""): card for card in cards if isinstance(card, dict)}
    dimensions = load_review_dimensions(repo_root)
    worksheets: list[dict[str, Any]] = []
    for case_id in GOLDEN_CASE_IDS:
        card = by_case.get(case_id)
        if card is None:
            errors.append(f"P10-4 missing P10-3 comparison card for {case_id}")
            continue
        if card.get("original_decision") != "request_rework":
            errors.append(f"P10-4 expected original request_rework decision for {case_id}, got {card.get('original_decision')!r}")
        worksheets.append(
            {
                "case_id": case_id,
                "title": card.get("title") or case_id,
                "original_p9_1b_decision": card.get("original_decision"),
                "post_p9_review_state": "pending_human_review",
                "allowed_decisions": ALLOWED_DECISIONS,
                "required_review_fields": REQUIRED_REVIEW_FIELDS,
                "review_dimensions": dimensions,
                "reviewer_id": None,
                "reviewed_at": None,
                "decision": None,
                "scores": {},
                "slide_level_findings": [],
                "follow_up_backlog": [],
                "comparison_card_digest": digest_payload(card),
                "original_blocker_finding_count": card.get("original_blocker_finding_count"),
                "original_warning_finding_count": card.get("original_warning_finding_count"),
                "post_p9_visual_qa_status": card.get("post_p9_visual_qa_status"),
                "post_p9_provenance_coverage_status": card.get("post_p9_provenance_coverage_status"),
                "requires_human_re_review": True,
                "operator_instruction": "Open the regenerated post-P9 artifact triplet and fill reviewer_id, reviewed_at, decision, scores, slide_level_findings, and follow_up_backlog before any approval-state change.",
            }
        )
    return worksheets, errors


def build_packet(repo_root: Path, artifacts_root: Path, comparison_payload: dict[str, Any], worksheets: list[dict[str, Any]]) -> dict[str, Any]:
    packet = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint": CHECKPOINT,
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_3": EXPECTED_BASE_AFTER_P10_3,
        "artifacts_root": str(artifacts_root),
        "comparison_report_digest": digest_payload(comparison_payload),
        "review_worksheet_count": len(worksheets),
        "review_worksheets": worksheets,
        "human_re_review_capture_packet_generated_by_p10_4": True,
        "human_re_review_completed_by_p10_4": False,
        "approval_state_changed_by_p10_4": False,
        "golden_decks_auto_approved_by_p10_4": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_4": False,
        "api_endpoint_added_by_p10_4": False,
        "db_schema_migration_added_by_p10_4": False,
        "frontend_runtime_changed_by_p10_4": False,
        "dependency_versions_changed_by_p10_4": False,
        "dockerfiles_changed_by_p10_4": False,
        "cloud_llm_added_by_p10_4": False,
        "cloud_vision_added_by_p10_4": False,
        "kimi_level_claimed_by_p10_4": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }
    packet["review_packet_digest"] = digest_payload(packet)
    return packet


def build_report_with_artifacts(repo_root: Path, artifacts_root: Path, persist_artifacts: bool, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    comparison_payload: dict[str, Any] | None = None
    worksheets: list[dict[str, Any]] = []
    packet: dict[str, Any] = {}
    returncode = 1
    if not errors:
        artifacts_root.mkdir(parents=True, exist_ok=True)
        comparison_payload, stdout, stderr, returncode = run_p10_3_comparison(repo_root, artifacts_root)
        if returncode != 0:
            errors.append(f"P10-3 comparison failed during P10-4 review capture with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if comparison_payload is None:
            errors.append("P10-4 could not parse P10-3 comparison JSON output")
        elif comparison_payload.get("status") != "ready":
            errors.append(f"P10-3 comparison status is not ready during P10-4 capture: {comparison_payload.get('status')}")
        if comparison_payload is not None:
            worksheets, worksheet_errors = build_review_worksheets(repo_root, comparison_payload)
            errors.extend(worksheet_errors)
            packet = build_packet(repo_root, artifacts_root, comparison_payload, worksheets)
            packet_path = artifacts_root / "p10_4_post_p9_human_re_review_packet.json"
            packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    ready = not errors and len(worksheets) == len(GOLDEN_CASE_IDS)
    return {
        "mode": "p10-4-post-p9-human-re-review-capture",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_3": EXPECTED_BASE_AFTER_P10_3,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "artifacts_root": str(artifacts_root),
        "review_packet_persisted": persist_artifacts,
        "p10_4_post_p9_human_re_review_capture_supported": True,
        "human_re_review_capture_packet_generated_by_p10_4": ready,
        "human_re_review_completed_by_p10_4": False,
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "review_worksheets": worksheets,
        "review_packet": packet,
        "review_packet_file": str(artifacts_root / "p10_4_post_p9_human_re_review_packet.json") if packet else None,
        "p10_3_comparison_returncode": returncode,
        "allowed_decisions": ALLOWED_DECISIONS,
        "required_review_fields": REQUIRED_REVIEW_FIELDS,
        "all_review_decisions_pending": bool(worksheets) and all(item.get("decision") is None for item in worksheets),
        "approval_state_changed_by_p10_4": False,
        "golden_decks_auto_approved_by_p10_4": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_4": False,
        "api_endpoint_added_by_p10_4": False,
        "db_schema_migration_added_by_p10_4": False,
        "frontend_runtime_changed_by_p10_4": False,
        "dependency_versions_changed_by_p10_4": False,
        "dockerfiles_changed_by_p10_4": False,
        "cloud_llm_added_by_p10_4": False,
        "cloud_vision_added_by_p10_4": False,
        "kimi_level_claimed_by_p10_4": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "next_recommended_step": "P10-5 - create a release decision dossier only after completed human re-review results are captured.",
    }


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    if artifacts_dir is not None:
        return build_report_with_artifacts(repo_root, artifacts_dir.resolve(), True, require_ready)
    with tempfile.TemporaryDirectory(prefix="kw_p10_4_post_p9_review_") as tmp:
        return build_report_with_artifacts(repo_root, Path(tmp), False, require_ready)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-4 post-P9 human re-review capture workflow.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-4 post-P9 human re-review capture: {report['status']}")
        print(f"review worksheets: {report['review_worksheet_count']}/{report['expected_review_worksheet_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
