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

CHECKPOINT = "P10-3"
EXPECTED_BASE_AFTER_P10_2 = "048443a073b807026a2de725e1d069f60a7e6a18"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_2_POST_P9_ARTIFACT_PACK.md",
    "docs/codex/P10_3_POST_P9_ARTIFACT_COMPARISON.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_p10_2_post_p9_artifact_pack.py",
    "scripts/kw_p10_3_post_p9_artifact_comparison.py",
    "backend/tests/smoke/test_p10_3_post_p9_artifact_comparison.py",
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

def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()

def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_2:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_2, head)
            if ancestry is False:
                errors.append(f"expected P10-2 baseline {EXPECTED_BASE_AFTER_P10_2} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-2 ancestry for {EXPECTED_BASE_AFTER_P10_2}..{head}")
    return errors

def run_p10_2_pack(repo_root: Path, artifacts_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    command = (sys.executable, "scripts/kw_p10_2_post_p9_artifact_pack.py", "--repo-root", str(repo_root), "--artifacts-dir", str(artifacts_root), "--require-ready", "--json")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode

def finding_summary(case: dict[str, Any]) -> dict[str, Any]:
    findings = case.get("slide_level_findings", []) if isinstance(case.get("slide_level_findings"), list) else []
    blockers = sum(1 for item in findings if isinstance(item, dict) and item.get("severity") == "blocker")
    warnings = sum(1 for item in findings if isinstance(item, dict) and item.get("severity") == "warning")
    return {
        "original_decision": case.get("decision"),
        "original_blocker_finding_count": blockers,
        "original_warning_finding_count": warnings,
        "original_visual_qa_score": case.get("visual_qa_score"),
        "original_visual_qa_status": case.get("visual_qa_status"),
        "original_provenance_coverage_status": case.get("provenance_coverage_status"),
    }

def load_artifacts(artifacts_root: Path, case_id: str) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    pptx = artifacts_root / case_id / f"rc1-{case_id}.pptx"
    manifest_path = artifacts_root / case_id / "manifest.json"
    metadata_path = artifacts_root / case_id / "safe_metadata.json"
    if not pptx.exists() or pptx.stat().st_size <= 0:
        errors.append(f"missing or empty generated PPTX for {case_id}")
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    metadata = load_json(metadata_path) if metadata_path.exists() else {}
    if not manifest:
        errors.append(f"missing generated manifest for {case_id}")
    if not metadata:
        errors.append(f"missing generated safe metadata for {case_id}")
    return manifest, metadata, errors

def build_cards(review_payload: dict[str, Any], pack_payload: dict[str, Any], artifacts_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    review_cases = review_payload.get("cases", []) if isinstance(review_payload.get("cases"), list) else []
    review_by_id = {str(case.get("case_id") or ""): case for case in review_cases if isinstance(case, dict)}
    generated = pack_payload.get("case_artifact_cards", []) if isinstance(pack_payload.get("case_artifact_cards"), list) else []
    generated_by_id = {str(card.get("case_id") or ""): card for card in generated if isinstance(card, dict)}
    cards: list[dict[str, Any]] = []
    for case_id in GOLDEN_CASE_IDS:
        original = review_by_id.get(case_id)
        generated_card = generated_by_id.get(case_id)
        if original is None or generated_card is None:
            errors.append(f"missing original or generated card for {case_id}")
            continue
        manifest, metadata, artifact_errors = load_artifacts(artifacts_root, case_id)
        errors.extend(artifact_errors)
        markers = tuple(sorted(k for k in metadata if k.startswith(("p9_", "semantic_", "operator_", "human_")))) if isinstance(metadata, dict) else ()
        cards.append({
            "case_id": case_id,
            "title": original.get("title") or case_id,
            **finding_summary(original),
            "post_p9_artifact_present": True,
            "post_p9_pptx_size_bytes": generated_card.get("pptx_size_bytes"),
            "post_p9_visual_qa_status": generated_card.get("visual_qa_status"),
            "post_p9_provenance_coverage_status": generated_card.get("provenance_coverage_status"),
            "post_p9_manifest_digest": digest_payload(manifest),
            "post_p9_safe_metadata_digest": digest_payload(metadata),
            "post_p9_safe_metadata_hardening_marker_count": len(markers),
            "post_p9_safe_metadata_hardening_markers": markers[:40],
            "requires_human_re_review": True,
            "approval_state_changed_by_p10_3": False,
            "comparison_instruction": "Compare this generated artifact against the listed original P9-1B blockers/warnings before changing the approval state.",
        })
    return cards, errors

def build_report_with_artifacts(repo_root: Path, artifacts_root: Path, persist_artifacts: bool, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    review_payload: dict[str, Any] = {}
    pack_payload: dict[str, Any] | None = None
    cards: list[dict[str, Any]] = []
    if not errors:
        review_payload = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
        artifacts_root.mkdir(parents=True, exist_ok=True)
        pack_payload, stdout, stderr, returncode = run_p10_2_pack(repo_root, artifacts_root)
        if returncode != 0:
            errors.append(f"P10-2 pack generation failed during P10-3 comparison with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if pack_payload is None:
            errors.append("P10-3 could not parse P10-2 pack JSON output")
        elif pack_payload.get("status") != "ready":
            errors.append(f"P10-2 pack status is not ready during P10-3 comparison: {pack_payload.get(status)}")
        if pack_payload is not None:
            cards, card_errors = build_cards(review_payload, pack_payload, artifacts_root)
            errors.extend(card_errors)
    summary = review_payload.get("human_review_summary", {}) if isinstance(review_payload.get("human_review_summary"), dict) else {}
    report = {
        "mode": "p10-3-post-p9-artifact-comparison",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": "p10.3.post_p9_artifact_comparison.v1",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_2": EXPECTED_BASE_AFTER_P10_2,
        "status": "ready" if not errors and len(cards) == len(GOLDEN_CASE_IDS) else "failed",
        "errors": errors,
        "artifacts_root": str(artifacts_root),
        "artifact_pack_persisted": persist_artifacts,
        "p10_3_post_p9_artifact_comparison_supported": True,
        "post_p9_artifacts_compared_to_p9_1b_findings": not errors and len(cards) == len(GOLDEN_CASE_IDS),
        "comparison_case_count": len(cards),
        "expected_comparison_case_count": len(GOLDEN_CASE_IDS),
        "original_request_rework_count": summary.get("decision_counts", {}).get("request_rework", 0),
        "original_approve_count": summary.get("decision_counts", {}).get("approve", 0),
        "case_comparison_cards": cards,
        "comparison_report_digest": digest_payload(cards),
        "human_re_review_required_after_p10_3": True,
        "approval_state_changed_by_p10_3": False,
        "golden_decks_auto_approved_by_p10_3": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_3": False,
        "api_endpoint_added_by_p10_3": False,
        "db_schema_migration_added_by_p10_3": False,
        "frontend_runtime_changed_by_p10_3": False,
        "dependency_versions_changed_by_p10_3": False,
        "dockerfiles_changed_by_p10_3": False,
        "cloud_llm_added_by_p10_3": False,
        "cloud_vision_added_by_p10_3": False,
        "kimi_level_claimed_by_p10_3": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "next_recommended_step": "P10-4 - run or capture a new human re-review using the comparison cards; do not auto-approve generated decks.",
    }
    if cards:
        comparison_path = artifacts_root / "p10_3_post_p9_artifact_comparison_report.json"
        comparison_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["comparison_report_file"] = str(comparison_path)
    return report

def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    if artifacts_dir is not None:
        return build_report_with_artifacts(repo_root, artifacts_dir.resolve(), True, require_ready)
    with tempfile.TemporaryDirectory(prefix="kw_p10_3_post_p9_compare_") as tmp:
        return build_report_with_artifacts(repo_root, Path(tmp), False, require_ready)

def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-3 post-P9 artifact comparison report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-3 post-P9 artifact comparison: {report[status]}")
        print(f"cases compared: {report[comparison_case_count]}/{report[expected_comparison_case_count]}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1

if __name__ == "__main__":
    raise SystemExit(main())
