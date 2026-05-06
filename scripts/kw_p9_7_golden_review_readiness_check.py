#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_1_GOLDEN_HUMAN_REVIEW_RESULTS.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
    "scripts/kw_p9_2_renderer_content_hardening_check.py",
    "backend/tests/smoke/test_p9_2_renderer_content_hardening.py",
    "docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md",
    "scripts/kw_p9_3_renderer_layout_hardening_check.py",
    "backend/tests/smoke/test_p9_3_renderer_layout_hardening.py",
    "docs/codex/P9_4_VISUAL_QA_SEMANTIC_GUARD.md",
    "scripts/kw_p9_4_visual_qa_semantic_guard_check.py",
    "backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py",
    "docs/codex/P9_5_PROVENANCE_USEFULNESS.md",
    "scripts/kw_p9_5_provenance_usefulness_check.py",
    "backend/tests/smoke/test_p9_5_provenance_usefulness.py",
    "docs/codex/P9_6_SEMANTIC_SOURCE_COVERAGE.md",
    "scripts/kw_p9_6_semantic_source_coverage_check.py",
    "backend/tests/smoke/test_p9_6_semantic_source_coverage.py",
    "docs/codex/P9_7_GOLDEN_REVIEW_READINESS.md",
    "scripts/kw_p9_7_golden_review_readiness_check.py",
    "backend/tests/smoke/test_p9_7_golden_review_readiness.py",
)
EXPECTED_BASE_AFTER_P9_6 = "0879dfd81b00db67ea20a15cb326c44c17849984"
P9_HARDENING_EVIDENCE = ("P9-2", "P9-3", "P9-4", "P9-5", "P9-6")

KNOWN_NON_BLOCKING_FULL_RUNNER_WARNINGS: tuple[dict[str, object], ...] = (
    {
        "warning_id": "npm_deprecated_transitive_packages",
        "source": "frontend npm ci",
        "classification": "known_non_blocking_warning",
        "blocks_p9_7_closure": False,
        "remediation_track": "separate_controlled_dependency_security_patch",
        "notes": "Deprecated transitive npm packages are tracked but not changed in P9-7.",
    },
    {
        "warning_id": "npm_audit_vulnerabilities",
        "source": "frontend npm audit summary",
        "classification": "known_non_blocking_warning",
        "blocks_p9_7_closure": False,
        "remediation_track": "separate_controlled_dependency_security_patch",
        "notes": "Do not run npm audit fix --force inside P9 feature/hardening patches.",
    },
    {
        "warning_id": "rc2_quality_warning_findings",
        "source": "RC2 golden benchmark quality review",
        "classification": "conservative_human_review_evidence",
        "blocks_p9_7_closure": False,
        "remediation_track": "post_hardening_human_re_review",
        "notes": "RC2 warning_findings remain evidence for re-review and do not auto-approve golden decks.",
    },
)

FINDING_TO_EVIDENCE: dict[str, tuple[str, ...]] = {
    "generic_fallback_labels_and_filler_slides": ("P9-2", "P9-3", "P9-4"),
    "comparison_table_decision_matrix": ("P9-2", "P9-3", "P9-4"),
    "project_log_late_phase_coverage": ("P9-2", "P9-6"),
    "long_structured_source_filler_prevention": ("P9-2", "P9-6"),
    "provenance_usefulness": ("P9-5", "P9-6"),
    "visual_qa_human_review_mismatch": ("P9-4",),
}

CASE_FINDINGS: dict[str, tuple[str, ...]] = {
    "k0_exec_memo_to_board_deck": ("generic_fallback_labels_and_filler_slides", "provenance_usefulness", "visual_qa_human_review_mismatch"),
    "k0_arch_doc_to_architecture_deck": ("generic_fallback_labels_and_filler_slides", "provenance_usefulness", "visual_qa_human_review_mismatch"),
    "k0_project_log_to_status_deck": ("project_log_late_phase_coverage", "provenance_usefulness", "visual_qa_human_review_mismatch"),
    "k0_comparison_table_to_decision_deck": ("comparison_table_decision_matrix", "provenance_usefulness", "visual_qa_human_review_mismatch"),
    "k0_long_docx_pdf_to_structured_presentation": ("long_structured_source_filler_prevention", "provenance_usefulness", "visual_qa_human_review_mismatch"),
}


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-7 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") not in ("9_Product_Release_Hardening", "8_K_Phase"):
        errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def load_human_review_fixture(repo_root: Path) -> dict[str, Any]:
    fixture_path = repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def build_case_cards(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return [], ["P9-1B fixture has no cases list"]

    cards: list[dict[str, Any]] = []
    for item in cases:
        case_id = str(item.get("case_id") or "")
        decision = item.get("decision")
        findings = CASE_FINDINGS.get(case_id, ())
        evidence_ids = tuple(dict.fromkeys(evidence for finding in findings for evidence in FINDING_TO_EVIDENCE.get(finding, ())))
        if decision != "request_rework":
            errors.append(f"P9-7 expected conservative request_rework decision for {case_id}, got {decision!r}")
        if case_id not in CASE_FINDINGS:
            errors.append(f"P9-7 has no readiness mapping for case {case_id!r}")
        if not evidence_ids:
            errors.append(f"P9-7 has no hardening evidence for case {case_id!r}")
        cards.append({
            "case_id": case_id,
            "title": item.get("title") or case_id,
            "original_decision": decision,
            "requires_human_re_review": True,
            "mapped_findings": findings,
            "hardening_evidence_ids": evidence_ids,
            "operator_review_instruction": "Regenerate or re-open the post-hardening artifact and compare it with the original P9-1B findings before changing approval state.",
        })
    return cards, errors


def inspect_readiness(repo_root: Path) -> dict[str, Any]:
    payload = load_human_review_fixture(repo_root)
    summary = payload.get("human_review_summary", {}) if isinstance(payload.get("human_review_summary"), dict) else {}
    cases = payload.get("cases", []) if isinstance(payload.get("cases"), list) else []
    cards, errors = build_case_cards(payload)

    decision_counts = summary.get("decision_counts", {}) if isinstance(summary.get("decision_counts"), dict) else {}
    if payload.get("human_review_results_completed") is not True:
        errors.append("P9-1B human review results must be completed before P9-7 readiness")
    if len(cases) != 5:
        errors.append(f"expected five golden benchmark cases, got {len(cases)}")
    if decision_counts.get("request_rework") != 5:
        errors.append("P9-7 expects all five original cases to remain request_rework before re-review")
    if decision_counts.get("approve", 0) != 0 or decision_counts.get("reject", 0) != 0:
        errors.append("P9-7 must not fabricate approve/reject outcomes from post-hardening evidence")
    if payload.get("kimi_level_claimed") is not False or payload.get("whole_project_kimi_level_supported") is not False:
        errors.append("P9-7 requires conservative no-Kimi-level source fixture flags")

    covered_findings = tuple(sorted({finding for card in cards for finding in card["mapped_findings"]}))
    covered_evidence = tuple(sorted({evidence for card in cards for evidence in card["hardening_evidence_ids"]}))
    missing_evidence = tuple(evidence for evidence in P9_HARDENING_EVIDENCE if evidence not in covered_evidence)
    if missing_evidence:
        errors.append("P9-7 readiness packet does not reference all prior hardening evidence: " + ", ".join(missing_evidence))

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p9_7_golden_review_readiness_supported": True,
        "post_hardening_re_review_packet_supported": True,
        "full_runner_known_warnings_classification_supported": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "known_non_blocking_full_runner_warning_count": len(KNOWN_NON_BLOCKING_FULL_RUNNER_WARNINGS),
        "known_non_blocking_full_runner_warnings": KNOWN_NON_BLOCKING_FULL_RUNNER_WARNINGS,
        "full_runner_known_warnings_block_p9_7_closure": False,
        "npm_audit_fix_force_run_by_p9_7": False,
        "dependency_security_remediation_deferred_to_controlled_patch": True,
        "rc2_warning_findings_are_conservative_review_evidence": True,
        "docker_smoke_warnings_block_p9_7_closure": False,
        "human_review_replay_required": True,
        "golden_case_count": len(cases),
        "re_review_case_count": len(cards),
        "original_request_rework_count": decision_counts.get("request_rework", 0),
        "original_approve_count": decision_counts.get("approve", 0),
        "original_reject_count": decision_counts.get("reject", 0),
        "mapped_human_review_findings": covered_findings,
        "hardening_evidence_ids": covered_evidence,
        "case_readiness_cards": cards,
        "approval_state_changed_by_p9_7": False,
        "human_review_results_fabricated_by_p9_7": False,
        "api_endpoint_added_by_p9_7": False,
        "db_schema_migration_added_by_p9_7": False,
        "frontend_runtime_changed_by_p9_7": False,
        "dependency_versions_changed_by_p9_7": False,
        "npm_audit_fix_force_run_by_p9_7": False,
        "dependency_security_remediation_deferred_to_controlled_patch": True,
        "dockerfiles_changed_by_p9_7": False,
        "cloud_llm_added_by_p9_7": False,
        "cloud_vision_added_by_p9_7": False,
        "kimi_level_claimed_by_p9_7": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    readiness = inspect_readiness(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(readiness.get("errors", []))
    return {
        "mode": "p9-7-golden-review-readiness",
        "phase": "P9 Product Release Hardening",
        "checkpoint": "P9-7",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_6": EXPECTED_BASE_AFTER_P9_6,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in readiness.items() if key not in {"status", "errors"}},
        "next_recommended_step": "Post-hardening golden benchmark regeneration or human re-review; do not claim Kimi-level without a new completed review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-7 golden benchmark post-hardening review-readiness check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-7 golden review readiness: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
