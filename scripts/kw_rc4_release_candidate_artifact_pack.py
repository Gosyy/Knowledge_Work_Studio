#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

RC4_CHECKPOINT = "RC4"
RC4_SCHEMA_VERSION = "rc4.release_candidate_artifact_pack.v1"
RC4_EXPECTED_BRANCH = "8_K_Phase"

NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_rc4": False,
    "db_schema_migration_added_by_rc4": False,
    "frontend_runtime_changed_by_rc4": False,
    "dependency_versions_changed_by_rc4": False,
    "dockerfiles_changed_by_rc4": False,
    "cloud_llm_added_by_rc4": False,
    "cloud_vision_added_by_rc4": False,
    "product_runtime_changed_by_rc4": False,
    "kimi_level_claimed_by_rc4": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class RC4PackItem:
    item_id: str
    phase: str
    evidence_type: str
    doc_path: str
    checker_path: str
    test_path: str
    artifact_role: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


PACK_ITEMS: tuple[RC4PackItem, ...] = (
    RC4PackItem("k0_rubric", "K0", "rubric", "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md", "scripts/kw_k0_kimi_rubric_check.py", "backend/tests/smoke/test_k0_kimi_rubric.py", "baseline_quality_rubric"),
    RC4PackItem("k1_planner", "K1", "runtime_checker", "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md", "scripts/kw_k1_local_gigachat_planner_check.py", "backend/tests/smoke/test_k1_local_gigachat_planner.py", "local_gigachat_planning_evidence"),
    RC4PackItem("k2_editor", "K2", "runtime_checker", "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md", "scripts/kw_k2_plan_editor_check.py", "backend/tests/smoke/test_k2_plan_editor_workflow.py", "plan_editor_workflow_evidence"),
    RC4PackItem("k3_renderer", "K3", "runtime_checker", "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md", "scripts/kw_k3_renderer_quality_check.py", "backend/tests/smoke/test_k3_renderer_quality_runtime.py", "renderer_quality_evidence"),
    RC4PackItem("k4_visual_qa", "K4", "runtime_checker", "docs/codex/K4_VISUAL_QA_RUNTIME.md", "scripts/kw_k4_visual_qa_check.py", "backend/tests/smoke/test_k4_visual_qa_runtime.py", "visual_qa_evidence"),
    RC4PackItem("k5_provenance", "K5", "runtime_checker", "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md", "scripts/kw_k5_source_to_slide_provenance_check.py", "backend/tests/smoke/test_k5_source_to_slide_provenance.py", "source_to_slide_provenance_evidence"),
    RC4PackItem("k6_end_to_end", "K6", "runtime_checker", "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md", "scripts/kw_k6_end_to_end_workflow_check.py", "backend/tests/smoke/test_k6_end_to_end_workflow.py", "end_to_end_workflow_evidence"),
    RC4PackItem("k_phase_closure", "K-phase", "closure_checker", "docs/codex/K_PHASE_RELEASE_READINESS_CHECKPOINT.md", "scripts/kw_k_phase_release_readiness_check.py", "backend/tests/smoke/test_k_phase_release_readiness_checkpoint.py", "release_readiness_checkpoint_evidence"),
    RC4PackItem("rc1_golden_execution", "RC1", "benchmark_harness", "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md", "scripts/kw_rc1_golden_benchmark_harness.py", "backend/tests/smoke/test_rc1_golden_benchmark_harness.py", "golden_benchmark_execution_evidence"),
    RC4PackItem("rc2_quality_review", "RC2", "quality_review", "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md", "scripts/kw_rc2_golden_benchmark_quality_review.py", "backend/tests/smoke/test_rc2_golden_benchmark_quality_review.py", "golden_quality_review_evidence"),
    RC4PackItem("rc3_gigachat_comparison", "RC3", "benchmark_comparison", "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md", "scripts/kw_rc3_local_gigachat_benchmark_comparison.py", "backend/tests/smoke/test_rc3_local_gigachat_benchmark_comparison.py", "gigachat_comparison_evidence"),
    RC4PackItem("rch1_renderer_hardening", "RCH1", "hardening_checker", "docs/codex/RCH1_RENDERER_DENSITY_LAYOUT_FIXES.md", "scripts/kw_rch1_renderer_density_layout_check.py", "backend/tests/smoke/test_rch1_renderer_density_layout_fixes.py", "renderer_density_layout_hardening_evidence"),
    RC4PackItem("rch2_provenance_hardening", "RCH2", "hardening_checker", "docs/codex/RCH2_PROVENANCE_FRAGMENT_QUALITY.md", "scripts/kw_rch2_provenance_fragment_quality_check.py", "backend/tests/smoke/test_rch2_provenance_fragment_quality.py", "provenance_fragment_quality_evidence"),
    RC4PackItem("rch3_visual_qa_hardening", "RCH3", "hardening_checker", "docs/codex/RCH3_VISUAL_QA_HEURISTIC_CALIBRATION.md", "scripts/kw_rch3_visual_qa_calibration_check.py", "backend/tests/smoke/test_rch3_visual_qa_calibration.py", "visual_qa_calibration_evidence"),
)



def _branch_is_allowed_for_p9(branch: str | None, expected_branch: str) -> bool:
    return branch == expected_branch or branch == "9_Product_Release_Hardening"

def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _collect_missing(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for item in PACK_ITEMS:
        for rel in (item.doc_path, item.checker_path, item.test_path):
            if not (repo_root / rel).exists():
                missing.append(rel)
    return sorted(set(missing))


def _inventory(repo_root: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for item in PACK_ITEMS:
        record = item.as_dict()
        record["files"] = []
        for rel in (item.doc_path, item.checker_path, item.test_path):
            path = repo_root / rel
            record["files"].append(
                {
                    "path": rel,
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else 0,
                    "digest": _file_digest(path) if path.exists() else None,
                }
            )
        inventory.append(record)
    return inventory


def _known_limitations() -> tuple[dict[str, object], ...]:
    return (
        {
            "limitation_id": "rc4.human_benchmark_review_required",
            "status": "open",
            "summary": "Golden benchmark automated reports do not replace human deck-quality review.",
            "release_blocker": False,
        },
        {
            "limitation_id": "rc4.local_server3_topology_not_reverified_by_rc4",
            "status": "open",
            "summary": "RC3 public development route does not verify the target offline Server 3 deployment topology.",
            "release_blocker": False,
        },
        {
            "limitation_id": "rc4.full_kimi_level_not_claimed",
            "status": "intentional",
            "summary": "Kimi-level remains a target; RC4 packages evidence and limitations without claiming whole-product parity.",
            "release_blocker": False,
        },
    )


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    commit = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    missing = _collect_missing(repo_root)
    errors: list[str] = []
    if require_ready and not _branch_is_allowed_for_p9(branch, RC4_EXPECTED_BRANCH):
        errors.append(f"expected branch {RC4_EXPECTED_BRANCH}, got {branch}")
    if missing:
        errors.extend(f"missing release-candidate artifact evidence file: {item}" for item in missing)

    inventory = _inventory(repo_root)
    inventory_digest = "sha256:" + sha256(
        json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    report: dict[str, Any] = {
        "mode": "rc4-release-candidate-artifact-pack",
        "phase": "K-phase release candidate",
        "checkpoint": RC4_CHECKPOINT,
        "schema_version": RC4_SCHEMA_VERSION,
        "branch": branch,
        "commit": commit,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "release_candidate_artifact_pack_supported": True,
        "artifact_inventory_supported": True,
        "machine_readable_pack_manifest_supported": True,
        "operator_release_notes_supported": True,
        "known_limitations_tracked": True,
        "human_benchmark_review_required": True,
        "offline_safe_default_required": True,
        "public_gigachat_dev_route_recorded_but_not_production_verified": True,
        "server3_offline_route_verification_required_before_production_claim": True,
        "pack_item_count": len(PACK_ITEMS),
        "artifact_file_count": sum(len(item["files"]) for item in inventory),
        "artifact_inventory_digest": inventory_digest,
        "artifact_inventory": inventory,
        "known_limitations": list(_known_limitations()),
        "next_recommended_step": "RC5 — release notes and operator handoff dry-run, or a controlled dependency/security patch if requested separately",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifacts_dir / "rc4-release-candidate-artifact-pack.json"
        md_path = artifacts_dir / "rc4-release-candidate-artifact-pack.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(report), encoding="utf-8")
        report["artifact_pack_outputs"] = {
            "json": str(json_path),
            "markdown": str(md_path),
        }
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# RC4 Release Candidate Artifact Pack",
        "",
        f"- status: `{report['status']}`",
        f"- branch: `{report['branch']}`",
        f"- commit: `{report['commit']}`",
        f"- pack items: `{report['pack_item_count']}`",
        f"- inventory digest: `{report['artifact_inventory_digest']}`",
        "",
        "## Pack items",
        "",
    ]
    for item in report["artifact_inventory"]:
        lines.append(f"- `{item['phase']}` `{item['item_id']}` — {item['artifact_role']}")
    lines.extend([
        "",
        "## Known limitations",
        "",
    ])
    for limitation in report["known_limitations"]:
        lines.append(f"- `{limitation['limitation_id']}`: {limitation['summary']}")
    lines.extend([
        "",
        "## Scope guard",
        "",
        "RC4 packages release-candidate evidence only. It does not add product runtime, API, DB, frontend, dependency, Docker, cloud LLM, cloud vision, or Kimi-level claim scope.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RC4 release candidate artifact pack checkpoint.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RC4 release candidate artifact pack: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
