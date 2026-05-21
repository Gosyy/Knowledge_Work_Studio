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

CHECKPOINT = "P10-2"
SCHEMA_VERSION = "p10.2.post_p9_artifact_pack.v1"
EXPECTED_BASE_AFTER_P10_1 = "2bc43dad0a55011c8627841b6fd5e2cc7be12f09"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P9_8_PRODUCT_RELEASE_HARDENING_CLOSURE.md",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "scripts/kw_p10_1_post_p9_regeneration_readiness_check.py",
    "scripts/kw_p10_2_post_p9_artifact_pack.py",
    "backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py",
    "backend/tests/smoke/test_p10_2_post_p9_artifact_pack.py",
    "docs/codex/P10_2_POST_P9_ARTIFACT_PACK.md",
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


def digest_file(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_1:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_1, head)
            if ancestry is False:
                errors.append(f"expected P10-1 baseline {EXPECTED_BASE_AFTER_P10_1} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-1 ancestry for {EXPECTED_BASE_AFTER_P10_1}..{head}")
    return errors


def verify_source_review_contract(repo_root: Path) -> list[str]:
    errors: list[str] = []
    review = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
    rc1_cases = load_json(repo_root / "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json")
    review_cases = review.get("cases", []) if isinstance(review, dict) else []
    review_ids = tuple(str(item.get("case_id") or "") for item in review_cases if isinstance(item, dict))
    rc1_ids = tuple(str(item.get("case_id") or "") for item in rc1_cases if isinstance(item, dict)) if isinstance(rc1_cases, list) else ()
    decision_counts = review.get("human_review_summary", {}).get("decision_counts", {}) if isinstance(review, dict) else {}
    if set(review_ids) != set(GOLDEN_CASE_IDS):
        errors.append(f"P10-2 expected P9-1B case ids {GOLDEN_CASE_IDS}, got {review_ids}")
    if set(rc1_ids) != set(GOLDEN_CASE_IDS):
        errors.append(f"P10-2 expected RC1 case ids {GOLDEN_CASE_IDS}, got {rc1_ids}")
    if decision_counts.get("request_rework") != 5 or decision_counts.get("approve", 0) != 0 or decision_counts.get("reject", 0) != 0:
        errors.append("P10-2 requires original P9-1B decisions to remain 5 request_rework, 0 approve, 0 reject")
    if review.get("kimi_level_claimed") is not False or review.get("whole_project_kimi_level_supported") is not False:
        errors.append("P10-2 requires conservative no-Kimi-level source fixture flags")
    return errors


def run_rc1_harness(repo_root: Path, artifacts_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    command = (
        sys.executable,
        "scripts/kw_rc1_golden_benchmark_harness.py",
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


def expected_triplet_paths(case_id: str) -> tuple[str, str, str]:
    return (
        f"{case_id}/rc1-{case_id}.pptx",
        f"{case_id}/manifest.json",
        f"{case_id}/safe_metadata.json",
    )


def inspect_generated_artifacts(artifacts_root: Path, rc1_report: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    cards: list[dict[str, Any]] = []
    report_by_case: dict[str, dict[str, Any]] = {}
    if rc1_report and isinstance(rc1_report.get("case_results"), list):
        for item in rc1_report["case_results"]:
            if isinstance(item, dict):
                report_by_case[str(item.get("case_id") or "")] = item
    for case_id in GOLDEN_CASE_IDS:
        paths = expected_triplet_paths(case_id)
        missing = [rel for rel in paths if not (artifacts_root / rel).exists()]
        if missing:
            errors.append(f"P10-2 missing generated artifacts for {case_id}: {missing}")
        pptx_path = artifacts_root / paths[0]
        manifest_path = artifacts_root / paths[1]
        metadata_path = artifacts_root / paths[2]
        if pptx_path.exists() and pptx_path.stat().st_size <= 0:
            errors.append(f"P10-2 generated empty PPTX for {case_id}")
        case_report = report_by_case.get(case_id, {})
        if case_report.get("status") not in ("passed", None):
            errors.append(f"P10-2 RC1 case did not pass: {case_id}: {case_report.get('errors')}")
        if case_report.get("automated_proxy_kimi_level_candidate_passed") is True:
            errors.append(f"P10-2 must not mark {case_id} as Kimi-level candidate without human review")
        cards.append(
            {
                "case_id": case_id,
                "artifact_paths": paths,
                "pptx_size_bytes": pptx_path.stat().st_size if pptx_path.exists() else 0,
                "pptx_checksum_sha256": digest_file(pptx_path) if pptx_path.exists() else None,
                "manifest_checksum_sha256": digest_file(manifest_path) if manifest_path.exists() else None,
                "safe_metadata_checksum_sha256": digest_file(metadata_path) if metadata_path.exists() else None,
                "rc1_status": case_report.get("status"),
                "visual_qa_status": case_report.get("visual_qa_status"),
                "provenance_coverage_status": case_report.get("provenance_coverage_status"),
                "requires_human_re_review": True,
            }
        )
    return cards, errors


def build_pack_manifest(repo_root: Path, artifacts_root: Path, cards: list[dict[str, Any]], rc1_report: dict[str, Any] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint": CHECKPOINT,
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_1": EXPECTED_BASE_AFTER_P10_1,
        "artifact_pack_root": str(artifacts_root),
        "golden_case_count": len(cards),
        "artifact_triplet_count": len(cards) * 3,
        "case_artifact_cards": cards,
        "rc1_harness_status": rc1_report.get("status") if isinstance(rc1_report, dict) else "unknown",
        "rc1_report_digest": digest_payload(rc1_report or {}),
        "post_p9_artifact_pack_generated_by_p10_2": True,
        "human_re_review_required_after_p10_2": True,
        "approval_state_changed_by_p10_2": False,
        "golden_decks_auto_approved_by_p10_2": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_2": False,
        "api_endpoint_added_by_p10_2": False,
        "db_schema_migration_added_by_p10_2": False,
        "frontend_runtime_changed_by_p10_2": False,
        "dependency_versions_changed_by_p10_2": False,
        "dockerfiles_changed_by_p10_2": False,
        "cloud_llm_added_by_p10_2": False,
        "cloud_vision_added_by_p10_2": False,
        "kimi_level_claimed_by_p10_2": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }
    payload["pack_manifest_digest"] = digest_payload(payload)
    return payload


def build_report_with_artifacts(repo_root: Path, artifacts_root: Path, persist_artifacts: bool, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    errors.extend(verify_source_review_contract(repo_root) if not errors else [])
    rc1_report: dict[str, Any] | None = None
    rc1_stdout = ""
    rc1_stderr = ""
    rc1_returncode = 1
    cards: list[dict[str, Any]] = []
    pack_manifest: dict[str, Any] = {}
    if not errors:
        artifacts_root.mkdir(parents=True, exist_ok=True)
        rc1_report, rc1_stdout, rc1_stderr, rc1_returncode = run_rc1_harness(repo_root, artifacts_root)
        if rc1_returncode != 0:
            errors.append(f"RC1 harness failed during P10-2 artifact generation with exit code {rc1_returncode}: {rc1_stderr.strip() or rc1_stdout.strip()[:500]}")
        if rc1_report is None:
            errors.append("P10-2 could not parse RC1 harness JSON output")
        if rc1_report and rc1_report.get("status") != "ready":
            errors.append(f"P10-2 RC1 harness status is not ready: {rc1_report.get('status')}")
        cards, artifact_errors = inspect_generated_artifacts(artifacts_root, rc1_report)
        errors.extend(artifact_errors)
        pack_manifest = build_pack_manifest(repo_root, artifacts_root, cards, rc1_report)
        manifest_path = artifacts_root / "p10_2_post_p9_artifact_pack_manifest.json"
        manifest_path.write_text(json.dumps(pack_manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    ready = not errors and len(cards) == len(GOLDEN_CASE_IDS)
    return {
        "mode": "p10-2-post-p9-golden-artifact-pack",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_1": EXPECTED_BASE_AFTER_P10_1,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "artifacts_root": str(artifacts_root),
        "artifact_pack_persisted": persist_artifacts,
        "post_p9_artifact_pack_generated_by_p10_2": ready,
        "p10_2_artifact_pack_manifest_supported": True,
        "golden_case_count": len(cards),
        "expected_golden_case_count": len(GOLDEN_CASE_IDS),
        "artifact_triplet_count": len(cards) * 3,
        "expected_artifact_triplet_count": len(GOLDEN_CASE_IDS) * 3,
        "case_artifact_cards": cards,
        "pack_manifest": pack_manifest,
        "pack_manifest_file": str(artifacts_root / "p10_2_post_p9_artifact_pack_manifest.json") if pack_manifest else None,
        "rc1_harness_status": rc1_report.get("status") if isinstance(rc1_report, dict) else None,
        "rc1_harness_returncode": rc1_returncode,
        "human_re_review_required_after_p10_2": True,
        "approval_state_changed_by_p10_2": False,
        "golden_decks_auto_approved_by_p10_2": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_2": False,
        "api_endpoint_added_by_p10_2": False,
        "db_schema_migration_added_by_p10_2": False,
        "frontend_runtime_changed_by_p10_2": False,
        "dependency_versions_changed_by_p10_2": False,
        "dockerfiles_changed_by_p10_2": False,
        "cloud_llm_added_by_p10_2": False,
        "cloud_vision_added_by_p10_2": False,
        "kimi_level_claimed_by_p10_2": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "next_recommended_step": "P10-3 - compare post-P9 generated artifacts against original P9-1B findings before any human approval-state change.",
    }


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    if artifacts_dir is not None:
        return build_report_with_artifacts(repo_root, artifacts_dir.resolve(), True, require_ready)
    with tempfile.TemporaryDirectory(prefix="kw_p10_2_post_p9_artifacts_") as tmp:
        return build_report_with_artifacts(repo_root, Path(tmp), False, require_ready)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-2 post-P9 golden artifact pack generation check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-2 post-P9 artifact pack: {report['status']}")
        print(f"golden cases: {report['golden_case_count']}/{report['expected_golden_case_count']}")
        print(f"artifact triplets: {report['artifact_triplet_count']}/{report['expected_artifact_triplet_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
