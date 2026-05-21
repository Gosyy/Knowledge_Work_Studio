#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_BASE_AFTER_P9_8 = "42d999a93a6328c1f35e8e3118b6bca6ab3f45ca"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_8_PRODUCT_RELEASE_HARDENING_CLOSURE.md",
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "scripts/kw_p10_1_post_p9_regeneration_readiness_check.py",
    "backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py",
)
P9_CLOSURE_FILES = (
    "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
    "docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md",
    "docs/codex/P9_4_VISUAL_QA_SEMANTIC_GUARD.md",
    "docs/codex/P9_5_PROVENANCE_USEFULNESS.md",
    "docs/codex/P9_6_SEMANTIC_SOURCE_COVERAGE.md",
    "docs/codex/P9_7_GOLDEN_REVIEW_READINESS.md",
    "docs/codex/P9_8_PRODUCT_RELEASE_HARDENING_CLOSURE.md",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-1 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    errors.extend(f"missing P9 closure evidence file: {rel}" for rel in P9_CLOSURE_FILES if not (repo_root / rel).exists())
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P9_8:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P9_8, head)
            if ancestry is False:
                errors.append(f"expected P9-8 baseline {EXPECTED_BASE_AFTER_P9_8} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P9-8 ancestry for {EXPECTED_BASE_AFTER_P9_8}..{head}")
    return errors


def inspect_readiness(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    review_payload = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
    rc1_cases = load_json(repo_root / "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json")
    cases = review_payload.get("cases", []) if isinstance(review_payload, dict) else []
    review_summary = review_payload.get("human_review_summary", {}) if isinstance(review_payload, dict) and isinstance(review_payload.get("human_review_summary"), dict) else {}

    review_case_ids = tuple(str(item.get("case_id") or "") for item in cases if isinstance(item, dict))
    rc1_case_ids = tuple(str(item.get("case_id") or "") for item in rc1_cases if isinstance(item, dict)) if isinstance(rc1_cases, list) else ()
    if set(review_case_ids) != set(GOLDEN_CASE_IDS):
        errors.append(f"P10-1 expected five P9-1B golden case ids, got {review_case_ids}")
    if set(rc1_case_ids) != set(GOLDEN_CASE_IDS):
        errors.append(f"P10-1 expected RC1 fixture case ids to match golden cases, got {rc1_case_ids}")
    if review_summary.get("decision_counts", {}).get("request_rework") != 5:
        errors.append("P10-1 requires all original P9-1B decisions to remain request_rework before re-review")
    if review_summary.get("decision_counts", {}).get("approve", 0) != 0:
        errors.append("P10-1 must not inherit any approved golden case before re-review")
    if review_payload.get("kimi_level_claimed") is not False or review_payload.get("whole_project_kimi_level_supported") is not False:
        errors.append("P10-1 requires conservative no-Kimi-level source fixture flags")

    regeneration_cases = []
    for case_id in GOLDEN_CASE_IDS:
        regeneration_cases.append(
            {
                "case_id": case_id,
                "source_fixture": "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
                "original_human_review_decision": "request_rework",
                "expected_outputs": (
                    f"{case_id}/post-p9-{case_id}.pptx",
                    f"{case_id}/manifest.json",
                    f"{case_id}/safe_metadata.json",
                ),
                "requires_human_re_review": True,
            }
        )

    expected_triplet_count = len(regeneration_cases) * 3
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p10_post_p9_phase_started": True,
        "p10_1_post_p9_regeneration_readiness_supported": True,
        "post_p9_golden_benchmark_regeneration_required": True,
        "post_p9_artifact_pack_generation_performed_by_p10_1": False,
        "human_re_review_required_after_regeneration": True,
        "golden_case_count": len(regeneration_cases),
        "expected_artifact_triplet_count": expected_triplet_count,
        "expected_artifact_file_count": expected_triplet_count,
        "regeneration_case_ids": tuple(case["case_id"] for case in regeneration_cases),
        "regeneration_cases": regeneration_cases,
        "source_fixture_case_ids_match_human_review_cases": set(review_case_ids) == set(rc1_case_ids) == set(GOLDEN_CASE_IDS),
        "original_request_rework_count": review_summary.get("decision_counts", {}).get("request_rework", 0),
        "original_approve_count": review_summary.get("decision_counts", {}).get("approve", 0),
        "original_reject_count": review_summary.get("decision_counts", {}).get("reject", 0),
        "p9_closure_evidence_required": tuple(f"P9-{index}" for index in range(1, 9)),
        "p9_closure_evidence_present": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "npm_audit_fix_force_run_by_p10_1": False,
        "approval_state_changed_by_p10_1": False,
        "golden_decks_auto_approved_by_p10_1": False,
        "api_endpoint_added_by_p10_1": False,
        "db_schema_migration_added_by_p10_1": False,
        "frontend_runtime_changed_by_p10_1": False,
        "dependency_versions_changed_by_p10_1": False,
        "dockerfiles_changed_by_p10_1": False,
        "cloud_llm_added_by_p10_1": False,
        "cloud_vision_added_by_p10_1": False,
        "kimi_level_claimed_by_p10_1": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    readiness = inspect_readiness(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(readiness.get("errors", []))
    return {
        "mode": "p10-1-post-p9-golden-regeneration-readiness",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": "P10-1",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_8": EXPECTED_BASE_AFTER_P9_8,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in readiness.items() if key not in {"status", "errors"}},
        "next_recommended_step": "P10-2 - generate post-P9 golden benchmark artifacts; do not change approval state until human re-review is complete.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-1 post-P9 golden regeneration readiness check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P10-1 post-P9 regeneration readiness: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
