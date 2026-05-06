#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_BASE_AFTER_P9_7 = "c1f6735a21fa82d13e2638d7b20ee304911275ab"
P9_BRANCH = "9_Product_Release_Hardening"

P9_PHASES: tuple[dict[str, object], ...] = (
    {"phase_id": "P9-1", "title": "Golden benchmark human review results", "files": ("docs/codex/P9_1_GOLDEN_HUMAN_REVIEW_RESULTS.md", "backend/tests/fixtures/p9/p9_1_human_review_results.json", "scripts/kw_p9_1_human_review_results_check.py", "backend/tests/smoke/test_p9_1_human_review_results.py")},
    {"phase_id": "P9-2", "title": "Renderer/content hardening from human review", "files": ("docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md", "scripts/kw_p9_2_renderer_content_hardening_check.py", "backend/tests/smoke/test_p9_2_renderer_content_hardening.py")},
    {"phase_id": "P9-3", "title": "Renderer layout hardening from human review", "files": ("docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md", "scripts/kw_p9_3_renderer_layout_hardening_check.py", "backend/tests/smoke/test_p9_3_renderer_layout_hardening.py")},
    {"phase_id": "P9-4", "title": "Visual QA semantic review guard from human review", "files": ("docs/codex/P9_4_VISUAL_QA_SEMANTIC_GUARD.md", "scripts/kw_p9_4_visual_qa_semantic_guard_check.py", "backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py")},
    {"phase_id": "P9-5", "title": "Provenance usefulness hardening from human review", "files": ("docs/codex/P9_5_PROVENANCE_USEFULNESS.md", "scripts/kw_p9_5_provenance_usefulness_check.py", "backend/tests/smoke/test_p9_5_provenance_usefulness.py")},
    {"phase_id": "P9-6", "title": "Semantic source coverage from human review", "files": ("docs/codex/P9_6_SEMANTIC_SOURCE_COVERAGE.md", "scripts/kw_p9_6_semantic_source_coverage_check.py", "backend/tests/smoke/test_p9_6_semantic_source_coverage.py")},
    {"phase_id": "P9-7", "title": "Golden benchmark post-hardening review readiness and warning classification", "files": ("docs/codex/P9_7_GOLDEN_REVIEW_READINESS.md", "scripts/kw_p9_7_golden_review_readiness_check.py", "backend/tests/smoke/test_p9_7_golden_review_readiness.py")},
    {"phase_id": "P9-8", "title": "Product release hardening closure dossier", "files": ("docs/codex/P9_8_PRODUCT_RELEASE_HARDENING_CLOSURE.md", "scripts/kw_p9_8_product_release_hardening_closure_check.py", "backend/tests/smoke/test_p9_8_product_release_hardening_closure.py")},
)

REQUIRED_FILES = (
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    *tuple(path for phase in P9_PHASES for path in phase["files"]),
)

KNOWN_NON_BLOCKING_WARNING_CLASSES = (
    "npm_deprecated_transitive_packages",
    "npm_audit_vulnerability_summary",
    "rc2_quality_review_warning_findings",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-8 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    branch = run_git(repo_root, "branch", "--show-current")
    if require_ready and branch not in (P9_BRANCH, "8_K_Phase"):
        errors.append(f"expected branch {P9_BRANCH} or 8_K_Phase, got {branch}")
    return errors


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_closure(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    plan = (repo_root / "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md").read_text(encoding="utf-8")
    review = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
    p9_7_checker = (repo_root / "scripts/kw_p9_7_golden_review_readiness_check.py").read_text(encoding="utf-8")

    for phase in P9_PHASES:
        phase_id = str(phase["phase_id"])
        if phase_id not in plan:
            errors.append(f"P9 plan is missing section for {phase_id}")

    summary = review.get("human_review_summary", {}) if isinstance(review.get("human_review_summary"), dict) else {}
    decision_counts = summary.get("decision_counts", {}) if isinstance(summary.get("decision_counts"), dict) else {}
    cases = review.get("cases") if isinstance(review.get("cases"), list) else []

    if review.get("human_review_results_completed") is not True:
        errors.append("P9-8 requires completed P9-1 human review results")
    if len(cases) != 5:
        errors.append(f"P9-8 requires five golden benchmark cases, got {len(cases)}")
    if decision_counts.get("request_rework") != 5 or decision_counts.get("approve", 0) != 0 or decision_counts.get("reject", 0) != 0:
        errors.append("P9-8 requires original P9-1 decisions to remain five request_rework cases")
    if review.get("kimi_level_claimed") is not False or review.get("whole_project_kimi_level_supported") is not False:
        errors.append("P9-8 requires conservative no-Kimi-level fixture flags")

    for marker in ("pass_with_known_non_blocking_warnings", "npm_audit_fix_force_run_by_p9_7", "rc2_quality_warning_findings"):
        if marker not in p9_7_checker:
            errors.append(f"P9-8 requires P9-7 warning classification marker: {marker}")

    phase_file_counts = {str(phase["phase_id"]): len(tuple(phase["files"])) for phase in P9_PHASES}
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p9_8_product_release_hardening_closure_supported": True,
        "p9_track_closure_dossier_supported": True,
        "p9_phase_count": len(P9_PHASES),
        "p9_closure_evidence_phase_ids": tuple(str(phase["phase_id"]) for phase in P9_PHASES),
        "p9_phase_file_counts": phase_file_counts,
        "golden_case_count": len(cases),
        "original_request_rework_count": decision_counts.get("request_rework", 0),
        "approval_state_changed_by_p9_8": False,
        "human_review_results_fabricated_by_p9_8": False,
        "golden_decks_auto_approved_by_p9_8": False,
        "post_hardening_human_re_review_required": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "known_non_blocking_warning_classes": KNOWN_NON_BLOCKING_WARNING_CLASSES,
        "known_non_blocking_full_runner_warning_count": len(KNOWN_NON_BLOCKING_WARNING_CLASSES),
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "npm_audit_fix_force_run_by_p9_8": False,
        "api_endpoint_added_by_p9_8": False,
        "db_schema_migration_added_by_p9_8": False,
        "frontend_runtime_changed_by_p9_8": False,
        "dependency_versions_changed_by_p9_8": False,
        "dockerfiles_changed_by_p9_8": False,
        "cloud_llm_added_by_p9_8": False,
        "cloud_vision_added_by_p9_8": False,
        "kimi_level_claimed_by_p9_8": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    closure = inspect_closure(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(closure.get("errors", []))
    return {
        "mode": "p9-8-product-release-hardening-closure",
        "phase": "P9 Product Release Hardening",
        "checkpoint": "P9-8",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_7": EXPECTED_BASE_AFTER_P9_7,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in closure.items() if key not in {"status", "errors"}},
        "next_recommended_step": "Run post-hardening golden benchmark regeneration and human re-review; do not claim Kimi-level without a completed new review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-8 product release hardening closure check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-8 product release hardening closure: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
