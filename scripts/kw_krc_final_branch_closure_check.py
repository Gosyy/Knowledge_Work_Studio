#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

KRC_CHECKPOINT = "KRC"
KRC_SCHEMA_VERSION = "krc.final_branch_closure.v1"
KRC_EXPECTED_BRANCH = "8_K_Phase"

NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_krc": False,
    "db_schema_migration_added_by_krc": False,
    "frontend_runtime_changed_by_krc": False,
    "dependency_versions_changed_by_krc": False,
    "dockerfiles_changed_by_krc": False,
    "cloud_llm_added_by_krc": False,
    "cloud_vision_added_by_krc": False,
    "product_runtime_changed_by_krc": False,
    "kimi_level_claimed_by_krc": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class ClosureItem:
    item_id: str
    phase: str
    status: str
    doc_path: str
    checker_path: str
    test_path: str
    closure_role: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


CLOSURE_ITEMS: tuple[ClosureItem, ...] = (
    ClosureItem("k0_rubric", "K0", "closed", "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md", "scripts/kw_k0_kimi_rubric_check.py", "backend/tests/smoke/test_k0_kimi_rubric.py", "quality_rubric_and_golden_cases"),
    ClosureItem("k1_planner", "K1", "closed", "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md", "scripts/kw_k1_local_gigachat_planner_check.py", "backend/tests/smoke/test_k1_local_gigachat_planner.py", "local_gigachat_first_planning"),
    ClosureItem("k2_plan_editor", "K2", "closed", "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md", "scripts/kw_k2_plan_editor_check.py", "backend/tests/smoke/test_k2_plan_editor_workflow.py", "operator_editable_plan_workflow"),
    ClosureItem("k3_renderer", "K3", "closed", "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md", "scripts/kw_k3_renderer_quality_check.py", "backend/tests/smoke/test_k3_renderer_quality_runtime.py", "renderer_quality_runtime"),
    ClosureItem("k4_visual_qa", "K4", "closed", "docs/codex/K4_VISUAL_QA_RUNTIME.md", "scripts/kw_k4_visual_qa_check.py", "backend/tests/smoke/test_k4_visual_qa_runtime.py", "local_visual_qa_runtime"),
    ClosureItem("k5_provenance", "K5", "closed", "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md", "scripts/kw_k5_source_to_slide_provenance_check.py", "backend/tests/smoke/test_k5_source_to_slide_provenance.py", "source_to_slide_provenance"),
    ClosureItem("k6_end_to_end", "K6", "closed", "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md", "scripts/kw_k6_end_to_end_workflow_check.py", "backend/tests/smoke/test_k6_end_to_end_workflow.py", "end_to_end_workflow_checkpoint"),
    ClosureItem("k_phase_closure", "K-phase", "closed", "docs/codex/K_PHASE_RELEASE_READINESS_CHECKPOINT.md", "scripts/kw_k_phase_release_readiness_check.py", "backend/tests/smoke/test_k_phase_release_readiness_checkpoint.py", "release_readiness_closure"),
    ClosureItem("rc1_golden_execution", "RC1", "accepted", "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md", "scripts/kw_rc1_golden_benchmark_harness.py", "backend/tests/smoke/test_rc1_golden_benchmark_harness.py", "golden_benchmark_execution"),
    ClosureItem("rc2_quality_review", "RC2", "accepted", "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md", "scripts/kw_rc2_golden_benchmark_quality_review.py", "backend/tests/smoke/test_rc2_golden_benchmark_quality_review.py", "quality_review_map"),
    ClosureItem("rc3_gigachat_comparison", "RC3", "accepted", "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md", "scripts/kw_rc3_local_gigachat_benchmark_comparison.py", "backend/tests/smoke/test_rc3_local_gigachat_benchmark_comparison.py", "gigachat_comparison_checkpoint"),
    ClosureItem("rc4_artifact_pack", "RC4", "accepted", "docs/codex/RC4_RELEASE_CANDIDATE_ARTIFACT_PACK.md", "scripts/kw_rc4_release_candidate_artifact_pack.py", "backend/tests/smoke/test_rc4_release_candidate_artifact_pack.py", "artifact_pack_inventory"),
    ClosureItem("rc5_dossier", "RC5", "accepted", "docs/codex/RC5_FINAL_RELEASE_READINESS_DOSSIER.md", "scripts/kw_rc5_final_release_readiness_dossier.py", "backend/tests/smoke/test_rc5_final_release_readiness_dossier.py", "final_release_dossier"),
    ClosureItem("rch1_renderer_hardening", "RCH1", "accepted", "docs/codex/RCH1_RENDERER_DENSITY_LAYOUT_FIXES.md", "scripts/kw_rch1_renderer_density_layout_check.py", "backend/tests/smoke/test_rch1_renderer_density_layout_fixes.py", "renderer_density_layout_hardening"),
    ClosureItem("rch2_provenance_hardening", "RCH2", "accepted", "docs/codex/RCH2_PROVENANCE_FRAGMENT_QUALITY.md", "scripts/kw_rch2_provenance_fragment_quality_check.py", "backend/tests/smoke/test_rch2_provenance_fragment_quality.py", "provenance_fragment_quality_hardening"),
    ClosureItem("rch3_visual_qa_hardening", "RCH3", "accepted", "docs/codex/RCH3_VISUAL_QA_HEURISTIC_CALIBRATION.md", "scripts/kw_rch3_visual_qa_calibration_check.py", "backend/tests/smoke/test_rch3_visual_qa_calibration.py", "visual_qa_calibration"),
    ClosureItem("rch4_human_review", "RCH4", "accepted", "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md", "scripts/kw_rch4_golden_benchmark_human_review.py", "backend/tests/smoke/test_rch4_golden_benchmark_human_review.py", "golden_benchmark_human_review_workflow"),
)

KRC_FILES = (
    "docs/codex/KRC_FINAL_BRANCH_CLOSURE.md",
    "scripts/kw_krc_final_branch_closure_check.py",
    "backend/tests/smoke/test_krc_final_branch_closure.py",
)


@dataclass(frozen=True)
class OpenRequirement:
    requirement_id: str
    status: str
    release_blocker: bool
    summary: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)



def _branch_is_allowed_for_p9(branch: str | None, expected_branch: str) -> bool:
    return branch == expected_branch or branch == "9_Product_Release_Hardening"

def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _open_requirements() -> tuple[OpenRequirement, ...]:
    return (
        OpenRequirement("krc.human_review_workflow_available_but_judgments_not_invented", "open_for_operator_execution", False, "RCH4 provides the human review workflow, but this closure does not invent completed human benchmark judgments."),
        OpenRequirement("krc.production_server3_gigachat_verification_separate", "open_for_production_topology", False, "RC3 public development route is not production Server 3 offline GigaChat evidence."),
        OpenRequirement("krc.dependency_security_remediation_separate_patch", "open_for_controlled_patch", False, "Known npm audit warnings remain a separate controlled dependency/security track."),
        OpenRequirement("krc.kimi_level_not_claimed", "intentional", False, "The branch is an accepted K/RC/RCH baseline toward the target; it does not claim whole-product Kimi-level parity."),
    )


def _closure_inventory(repo_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for item in CLOSURE_ITEMS:
        payload = item.as_dict()
        payload["files"] = []
        for rel in (item.doc_path, item.checker_path, item.test_path):
            path = repo_root / rel
            payload["files"].append({"path": rel, "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0, "digest": _file_digest(path) if path.exists() else None})
        records.append(payload)
    return records


def _missing_files(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for item in CLOSURE_ITEMS:
        for rel in (item.doc_path, item.checker_path, item.test_path):
            if not (repo_root / rel).exists():
                missing.append(rel)
    for rel in KRC_FILES:
        if not (repo_root / rel).exists():
            missing.append(rel)
    return sorted(set(missing))


def _production_gate_errors(repo_root: Path) -> list[str]:
    gate_path = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate_path.exists():
        return ["missing production readiness gate"]
    gate_text = gate_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for rel in KRC_FILES:
        if rel not in gate_text:
            errors.append(f"production readiness gate does not require KRC file: {rel}")
    if "K/RC final branch closure" not in gate_text:
        errors.append("production readiness gate does not execute KRC checker")
    return errors


def _inventory_digest(inventory: list[dict[str, object]]) -> str:
    encoded = json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    commit = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    inventory = _closure_inventory(repo_root)
    errors: list[str] = []
    if require_ready and not _branch_is_allowed_for_p9(branch, KRC_EXPECTED_BRANCH):
        errors.append(f"expected branch {KRC_EXPECTED_BRANCH}, got {branch}")
    errors.extend(f"missing final branch closure evidence file: {rel}" for rel in _missing_files(repo_root))
    errors.extend(_production_gate_errors(repo_root))
    phases = {item["phase"] for item in inventory}
    report: dict[str, Any] = {
        "mode": "krc-final-branch-closure",
        "phase": "K/RC branch closure",
        "checkpoint": KRC_CHECKPOINT,
        "schema_version": KRC_SCHEMA_VERSION,
        "branch": branch,
        "commit": commit,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "final_branch_closure_supported": True,
        "accepted_release_candidate_baseline": not errors,
        "branch_ready_for_next_phase_planning": not errors,
        "k_phase_checkpoints_closed": {"K0", "K1", "K2", "K3", "K4", "K5", "K6"}.issubset(phases),
        "rc_checkpoints_accepted": {"RC1", "RC2", "RC3", "RC4", "RC5"}.issubset(phases),
        "rch_checkpoints_accepted": {"RCH1", "RCH2", "RCH3", "RCH4"}.issubset(phases),
        "production_readiness_gate_includes_krc": not _production_gate_errors(repo_root),
        "closure_item_count": len(CLOSURE_ITEMS),
        "closure_file_count": len(CLOSURE_ITEMS) * 3 + len(KRC_FILES),
        "closure_inventory_digest": _inventory_digest(inventory),
        "closure_inventory": inventory,
        "open_requirements": [item.as_dict() for item in _open_requirements()],
        "human_review_workflow_available": True,
        "human_review_judgments_completed_by_krc": False,
        "server3_offline_gigachat_verification_completed_by_krc": False,
        "dependency_security_remediation_completed_by_krc": False,
        "next_recommended_step": "Create the next branch for operator release work, run RCH4 human review, or schedule a separate controlled dependency/security patch.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifacts_dir / "krc-final-branch-closure.json"
        md_path = artifacts_dir / "krc-final-branch-closure.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(report), encoding="utf-8")
        report["closure_outputs"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = ["# K/RC Final Branch Closure", "", f"- status: `{report['status']}`", f"- branch: `{report['branch']}`", f"- commit: `{report['commit']}`", f"- closure items: `{report['closure_item_count']}`", f"- inventory digest: `{report['closure_inventory_digest']}`", "", "## Closed / accepted checkpoints", ""]
    for item in report["closure_inventory"]:
        lines.append(f"- `{item['phase']}` `{item['item_id']}` - {item['status']} - {item['closure_role']}")
    lines.extend(["", "## Open requirements intentionally not closed here", ""])
    for item in report["open_requirements"]:
        lines.append(f"- `{item['requirement_id']}`: {item['summary']}")
    lines.extend(["", "## Scope guard", "", "KRC final branch closure is a branch-closure checkpoint only. It does not add product runtime, API, DB, frontend, dependency, Docker, cloud LLM, cloud vision, or Kimi-level claim scope.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K/RC final branch closure checkpoint.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"K/RC final branch closure: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
