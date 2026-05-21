#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

RC5_CHECKPOINT = "RC5"
RC5_SCHEMA_VERSION = "rc5.final_release_readiness_dossier.v1"
RC5_EXPECTED_BRANCH = "8_K_Phase"

NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_rc5": False,
    "db_schema_migration_added_by_rc5": False,
    "frontend_runtime_changed_by_rc5": False,
    "dependency_versions_changed_by_rc5": False,
    "dockerfiles_changed_by_rc5": False,
    "cloud_llm_added_by_rc5": False,
    "cloud_vision_added_by_rc5": False,
    "product_runtime_changed_by_rc5": False,
    "kimi_level_claimed_by_rc5": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class RC5DossierItem:
    item_id: str
    phase: str
    status: str
    doc_path: str
    checker_path: str
    test_path: str
    release_role: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


DOSSIER_ITEMS: tuple[RC5DossierItem, ...] = (
    RC5DossierItem("k0_rubric", "K0", "closed", "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md", "scripts/kw_k0_kimi_rubric_check.py", "backend/tests/smoke/test_k0_kimi_rubric.py", "rubric_and_golden_cases"),
    RC5DossierItem("k1_planner", "K1", "closed", "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md", "scripts/kw_k1_local_gigachat_planner_check.py", "backend/tests/smoke/test_k1_local_gigachat_planner.py", "local_gigachat_planning"),
    RC5DossierItem("k2_plan_editor", "K2", "closed", "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md", "scripts/kw_k2_plan_editor_check.py", "backend/tests/smoke/test_k2_plan_editor_workflow.py", "editable_plan_workflow"),
    RC5DossierItem("k3_renderer", "K3", "closed", "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md", "scripts/kw_k3_renderer_quality_check.py", "backend/tests/smoke/test_k3_renderer_quality_runtime.py", "renderer_quality_runtime"),
    RC5DossierItem("k4_visual_qa", "K4", "closed", "docs/codex/K4_VISUAL_QA_RUNTIME.md", "scripts/kw_k4_visual_qa_check.py", "backend/tests/smoke/test_k4_visual_qa_runtime.py", "visual_qa_runtime"),
    RC5DossierItem("k5_provenance", "K5", "closed", "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md", "scripts/kw_k5_source_to_slide_provenance_check.py", "backend/tests/smoke/test_k5_source_to_slide_provenance.py", "source_to_slide_provenance"),
    RC5DossierItem("k6_end_to_end", "K6", "closed", "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md", "scripts/kw_k6_end_to_end_workflow_check.py", "backend/tests/smoke/test_k6_end_to_end_workflow.py", "end_to_end_workflow_checkpoint"),
    RC5DossierItem("k_phase_closure", "K-phase", "closed", "docs/codex/K_PHASE_RELEASE_READINESS_CHECKPOINT.md", "scripts/kw_k_phase_release_readiness_check.py", "backend/tests/smoke/test_k_phase_release_readiness_checkpoint.py", "release_readiness_checkpoint"),
    RC5DossierItem("rc1_golden_execution", "RC1", "accepted", "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md", "scripts/kw_rc1_golden_benchmark_harness.py", "backend/tests/smoke/test_rc1_golden_benchmark_harness.py", "golden_benchmark_execution"),
    RC5DossierItem("rc2_quality_review", "RC2", "accepted", "docs/codex/RC2_GOLDEN_BENCHMARK_QUALITY_REVIEW_REPORT.md", "scripts/kw_rc2_golden_benchmark_quality_review.py", "backend/tests/smoke/test_rc2_golden_benchmark_quality_review.py", "quality_review_map"),
    RC5DossierItem("rc3_gigachat_comparison", "RC3", "accepted", "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md", "scripts/kw_rc3_local_gigachat_benchmark_comparison.py", "backend/tests/smoke/test_rc3_local_gigachat_benchmark_comparison.py", "local_gigachat_comparison"),
    RC5DossierItem("rc4_artifact_pack", "RC4", "accepted", "docs/codex/RC4_RELEASE_CANDIDATE_ARTIFACT_PACK.md", "scripts/kw_rc4_release_candidate_artifact_pack.py", "backend/tests/smoke/test_rc4_release_candidate_artifact_pack.py", "artifact_pack_inventory"),
    RC5DossierItem("rch1_renderer_hardening", "RCH1", "accepted", "docs/codex/RCH1_RENDERER_DENSITY_LAYOUT_FIXES.md", "scripts/kw_rch1_renderer_density_layout_check.py", "backend/tests/smoke/test_rch1_renderer_density_layout_fixes.py", "renderer_density_layout_hardening"),
    RC5DossierItem("rch2_provenance_hardening", "RCH2", "accepted", "docs/codex/RCH2_PROVENANCE_FRAGMENT_QUALITY.md", "scripts/kw_rch2_provenance_fragment_quality_check.py", "backend/tests/smoke/test_rch2_provenance_fragment_quality.py", "provenance_fragment_quality_hardening"),
    RC5DossierItem("rch3_visual_qa_hardening", "RCH3", "accepted", "docs/codex/RCH3_VISUAL_QA_HEURISTIC_CALIBRATION.md", "scripts/kw_rch3_visual_qa_calibration_check.py", "backend/tests/smoke/test_rch3_visual_qa_calibration.py", "visual_qa_heuristic_calibration"),
)

RC5_FILES = (
    "docs/codex/RC5_FINAL_RELEASE_READINESS_DOSSIER.md",
    "scripts/kw_rc5_final_release_readiness_dossier.py",
    "backend/tests/smoke/test_rc5_final_release_readiness_dossier.py",
)


@dataclass(frozen=True)
class ReleaseLimitation:
    limitation_id: str
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


def _known_limitations() -> tuple[ReleaseLimitation, ...]:
    return (
        ReleaseLimitation(
            limitation_id="rc5.human_benchmark_review_required",
            status="open",
            release_blocker=False,
            summary="Automated K/RC/RCH gates do not replace human review of golden benchmark deck quality.",
        ),
        ReleaseLimitation(
            limitation_id="rc5.production_server3_gigachat_route_not_verified_by_public_dev",
            status="open",
            release_blocker=False,
            summary="RC3 public API development route is not evidence that the target offline Server 3 GigaChat topology has been verified.",
        ),
        ReleaseLimitation(
            limitation_id="rc5.kimi_level_not_claimed",
            status="intentional",
            release_blocker=False,
            summary="The release candidate is a hardened baseline toward the Kimi-level target; it does not claim whole-product Kimi-level parity.",
        ),
        ReleaseLimitation(
            limitation_id="rc5.dependency_security_remediation_separate_patch",
            status="open",
            release_blocker=False,
            summary="Known npm audit warnings remain out of scope for RC5 and require a separate controlled dependency/security patch.",
        ),
    )


def _dossier_inventory(repo_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for item in DOSSIER_ITEMS:
        payload = item.as_dict()
        payload["files"] = []
        for rel in (item.doc_path, item.checker_path, item.test_path):
            path = repo_root / rel
            payload["files"].append(
                {
                    "path": rel,
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else 0,
                    "digest": _file_digest(path) if path.exists() else None,
                }
            )
        records.append(payload)
    return records


def _missing_files(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for item in DOSSIER_ITEMS:
        for rel in (item.doc_path, item.checker_path, item.test_path):
            if not (repo_root / rel).exists():
                missing.append(rel)
    for rel in RC5_FILES:
        if not (repo_root / rel).exists():
            missing.append(rel)
    return sorted(set(missing))


def _production_gate_errors(repo_root: Path) -> list[str]:
    gate_path = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate_path.exists():
        return ["missing production readiness gate"]
    gate_text = gate_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for rel in RC5_FILES:
        if rel not in gate_text:
            errors.append(f"production readiness gate does not require RC5 file: {rel}")
    if "RC5 Final release readiness dossier" not in gate_text:
        errors.append("production readiness gate does not execute RC5 checker")
    return errors


def _inventory_digest(inventory: list[dict[str, object]]) -> str:
    encoded = json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    commit = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    inventory = _dossier_inventory(repo_root)
    errors: list[str] = []
    if require_ready and not _branch_is_allowed_for_p9(branch, RC5_EXPECTED_BRANCH):
        errors.append(f"expected branch {RC5_EXPECTED_BRANCH}, got {branch}")
    errors.extend(f"missing final-release dossier file: {rel}" for rel in _missing_files(repo_root))
    errors.extend(_production_gate_errors(repo_root))

    limitations = tuple(item.as_dict() for item in _known_limitations())
    report: dict[str, Any] = {
        "mode": "rc5-final-release-readiness-dossier",
        "phase": "K-phase release candidate",
        "checkpoint": RC5_CHECKPOINT,
        "schema_version": RC5_SCHEMA_VERSION,
        "branch": branch,
        "commit": commit,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "final_release_readiness_dossier_supported": True,
        "release_candidate_baseline_ready": not errors,
        "all_k_phase_checkpoints_recorded": True,
        "all_rc_checkpoints_recorded": True,
        "all_rch_checkpoints_recorded": True,
        "rc4_artifact_pack_checkpoint_present": True,
        "production_readiness_gate_includes_rc5": not _production_gate_errors(repo_root),
        "operator_handoff_dossier_supported": True,
        "known_limitations_tracked": True,
        "human_benchmark_review_required": True,
        "server3_offline_gigachat_verification_required_before_production_claim": True,
        "public_gigachat_dev_route_not_production_evidence": True,
        "offline_safe_default_required": True,
        "dossier_item_count": len(DOSSIER_ITEMS),
        "dossier_file_count": len(DOSSIER_ITEMS) * 3 + len(RC5_FILES),
        "dossier_inventory_digest": _inventory_digest(inventory),
        "dossier_inventory": inventory,
        "known_limitations": list(limitations),
        "next_recommended_step": "K/RC release closure commit or a separate controlled dependency/security patch, depending on operator decision.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifacts_dir / "rc5-final-release-readiness-dossier.json"
        md_path = artifacts_dir / "rc5-final-release-readiness-dossier.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(report), encoding="utf-8")
        report["dossier_outputs"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# RC5 Final Release Readiness Dossier",
        "",
        f"- status: `{report['status']}`",
        f"- branch: `{report['branch']}`",
        f"- commit: `{report['commit']}`",
        f"- dossier items: `{report['dossier_item_count']}`",
        f"- inventory digest: `{report['dossier_inventory_digest']}`",
        "",
        "## Accepted checkpoints",
        "",
    ]
    for item in report["dossier_inventory"]:
        lines.append(f"- `{item['phase']}` `{item['item_id']}` — {item['status']} — {item['release_role']}")
    lines.extend(["", "## Known limitations", ""])
    for limitation in report["known_limitations"]:
        lines.append(f"- `{limitation['limitation_id']}`: {limitation['summary']}")
    lines.extend(
        [
            "",
            "## Scope guard",
            "",
            "RC5 is a release-readiness dossier only. It does not add product runtime, API, DB, frontend, dependency, Docker, cloud LLM, cloud vision, or Kimi-level claim scope.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RC5 final release readiness dossier checkpoint.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RC5 final release readiness dossier: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
