#!/usr/bin/env python3
"""KR-3E active gate legacy stage baseline-pin retirement checker.

This checker validates the KR-3E rule: legacy stage baseline-pinned
checkers remain in the repository as historical safety-net material, but the
production readiness gate must no longer actively require or execute them.
Product/refactor replacement checks must be the active gate contract instead.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RETIRED_ACTIVE_GATE_SCRIPTS: tuple[str, ...] = (
    "scripts/kw_p9_1_human_review_results_check.py",
    "scripts/kw_k0_kimi_rubric_check.py",
    "scripts/kw_k2_plan_editor_check.py",
    "scripts/kw_k3_renderer_quality_check.py",
    "scripts/kw_k4_visual_qa_check.py",
    "scripts/kw_k5_source_to_slide_provenance_check.py",
    "scripts/kw_k6_end_to_end_workflow_check.py",
    "scripts/kw_kq1_deck_quality_check.py",
    "scripts/kw_p10_10_final_release_approval_dossier.py",
    "scripts/kw_p10_11_final_operator_release_closure.py",
    "scripts/kw_p10_1_post_p9_regeneration_readiness_check.py",
    "scripts/kw_p10_2_post_p9_artifact_pack.py",
    "scripts/kw_k_phase_release_readiness_check.py",
)

REQUIRED_ACTIVE_REPLACEMENT_CHECKS: tuple[str, ...] = (
    "scripts/kw_kr_product_reset_roadmap_check.py",
    "scripts/kw_active_gate_legacy_retirement_check.py",
    "scripts/kw_product_test_aliases_check.py",
    "scripts/kw_low_risk_operator_static_replacements_check.py",
    "scripts/kw_slides_product_quality_replacements_check.py",
    "scripts/kw_docx_pdf_xlsx_product_workflows_check.py",
    "scripts/kw_path_portability_policy_check.py",
    "scripts/kw_path_portability_cleanup_plan.py",
    "scripts/kw_legacy_stage_baseline_pin_retirement.py",
)

REQUIRED_POLICY_FILES: tuple[str, ...] = (
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
    "docs/refactor/ACTIVE_GATE_LEGACY_RETIREMENT.md",
    "scripts/kw_active_gate_legacy_retirement_check.py",
    "backend/tests/integrations/test_active_gate_legacy_retirement.py",
    "backend/tests/smoke/test_active_gate_legacy_retirement.py",
)

LEGACY_ASSET_MARKERS: tuple[str, ...] = (
    "docs/codex/",
    "backend/tests/smoke/",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    gate_path = repo_root / "scripts" / "kw_production_readiness_gate.py"
    gate_text = read_text(gate_path)

    missing_policy_files = [rel for rel in REQUIRED_POLICY_FILES if not (repo_root / rel).exists()]
    retired_still_in_gate = [rel for rel in RETIRED_ACTIVE_GATE_SCRIPTS if rel in gate_text]
    missing_replacement_checks = [rel for rel in REQUIRED_ACTIVE_REPLACEMENT_CHECKS if rel not in gate_text]
    missing_retired_script_files = [rel for rel in RETIRED_ACTIVE_GATE_SCRIPTS if not (repo_root / rel).exists()]

    policy_doc = read_text(repo_root / "docs" / "refactor" / "ACTIVE_GATE_LEGACY_RETIREMENT.md")
    policy_markers = (
        "legacy scripts are not deleted",
        "docs/codex is not moved",
        "product/refactor replacement checks",
        "production readiness gate",
    )
    missing_policy_markers = [marker for marker in policy_markers if marker not in policy_doc]

    issues: list[str] = []
    if not gate_path.exists():
        issues.append("missing production readiness gate")
    issues.extend(f"missing KR-3E policy/check file: {rel}" for rel in missing_policy_files)
    issues.extend(f"retired legacy stage checker still active in production gate: {rel}" for rel in retired_still_in_gate)
    issues.extend(f"replacement product/refactor check missing from production gate: {rel}" for rel in missing_replacement_checks)
    issues.extend(f"retired legacy script was deleted instead of retained as safety-net history: {rel}" for rel in missing_retired_script_files)
    issues.extend(f"ACTIVE_GATE_LEGACY_RETIREMENT.md missing policy marker: {marker}" for marker in missing_policy_markers)

    return {
        "status": "ready" if not issues else "blocked",
        "purpose": "KR-3E removes active production-gate references to legacy stage baseline-pinned scripts without deleting legacy history.",
        "production_gate": "scripts/kw_production_readiness_gate.py",
        "retired_active_gate_scripts_total": len(RETIRED_ACTIVE_GATE_SCRIPTS),
        "retired_still_in_gate_count": len(retired_still_in_gate),
        "retired_still_in_gate": retired_still_in_gate,
        "retired_scripts_retained_count": len(RETIRED_ACTIVE_GATE_SCRIPTS) - len(missing_retired_script_files),
        "missing_retired_script_files": missing_retired_script_files,
        "required_replacement_checks_total": len(REQUIRED_ACTIVE_REPLACEMENT_CHECKS),
        "missing_replacement_checks_count": len(missing_replacement_checks),
        "missing_replacement_checks": missing_replacement_checks,
        "required_policy_files_total": len(REQUIRED_POLICY_FILES),
        "missing_policy_files": missing_policy_files,
        "missing_policy_markers": missing_policy_markers,
        "legacy_assets_retained": all((repo_root / marker).exists() for marker in LEGACY_ASSET_MARKERS),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-3E active gate legacy retirement: {report['status']}")
        if report["issues"]:
            print("Issues:")
            for issue in report["issues"]:
                print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
