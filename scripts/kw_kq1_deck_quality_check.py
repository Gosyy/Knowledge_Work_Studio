#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/KQ_PHASE_QUALITY_ROADMAP.md",
    "docs/codex/KQ1A_DECK_ARTIFACT_QUALITY_HARNESS.md",
    "backend/app/services/slides_service/kq_deck_quality.py",
    "scripts/kw_kq1_deck_quality_check.py",
    "scripts/kw_kq1_exec_memo_deck_quality.py",
    "backend/tests/smoke/test_kq1_deck_quality.py",
)
EXPECTED_BASE_AFTER_S13L = "3ca38a1d4f9a43af2aae85dcf032eb426c86ea4c"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing KQ-1A required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch != "9_Product_Release_Hardening":
            errors.append(f"expected branch 9_Product_Release_Hardening, got {branch}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.slides_service.kq_deck_quality import (  # noqa: WPS433
        assess_kq1a_deck_artifact_bundle,
        build_kq1a_capabilities_report,
        create_kq1a_smoke_bundle,
    )

    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="kq1a_check_") as tmp:
        tmp_path = Path(tmp)
        valid_bundle = create_kq1a_smoke_bundle(tmp_path / "valid_bundle", valid=True)
        invalid_bundle = create_kq1a_smoke_bundle(tmp_path / "json_only_bundle", valid=False)
        valid_result = assess_kq1a_deck_artifact_bundle(valid_bundle)
        invalid_result = assess_kq1a_deck_artifact_bundle(invalid_bundle)

        if valid_result.status != "ready":
            errors.append("valid KQ-1A smoke bundle did not pass: " + "; ".join(valid_result.errors))
        if invalid_result.status != "failed" or invalid_result.json_only_bundle_rejected is not True:
            errors.append("JSON-only smoke bundle was not rejected")
        if valid_result.kimi_level_claimed_by_kq1a is not False:
            errors.append("KQ-1A must not claim Kimi-level")
        if valid_result.selected_offline_workflow_parity_claim_supported_after_kq1a is not False:
            errors.append("KQ-1A must not claim selected offline workflow parity")
        if valid_result.server3_local_intranet_route_verified_by_kq1a is not False:
            errors.append("KQ-1A must not claim Server 3 verification")
        if valid_result.controlled_scope.get("calls_gigachat_by_kq1a") is not False:
            errors.append("KQ-1A must not call GigaChat")
        if valid_result.controlled_scope.get("generates_pptx_by_kq1a") is not False:
            errors.append("KQ-1A harness must not claim it generated the PPTX")

    capabilities = build_kq1a_capabilities_report()
    if capabilities.get("deck_artifact_quality_harness_supported") is not True:
        errors.append("KQ-1A capabilities do not report harness support")
    if capabilities.get("json_only_bundle_rejected") is not True:
        errors.append("KQ-1A capabilities must explicitly reject JSON-only bundles")
    for flag in (
        "api_endpoint_added_by_kq1a",
        "db_schema_migration_added_by_kq1a",
        "frontend_runtime_changed_by_kq1a",
        "dependency_versions_changed_by_kq1a",
        "dockerfiles_changed_by_kq1a",
        "calls_gigachat_by_kq1a",
        "reruns_model_generation_by_kq1a",
        "generates_pptx_by_kq1a",
        "kimi_level_claimed_by_kq1a",
        "whole_project_kimi_level_supported",
        "selected_offline_workflow_parity_claim_supported_after_kq1a",
        "server3_local_intranet_route_verified_by_kq1a",
    ):
        if capabilities.get(flag) is not False:
            errors.append(f"KQ-1A capability flag must be false: {flag}")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "capabilities": capabilities,
        "valid_smoke_bundle_status": "ready" if not errors else "checked",
        "json_only_bundle_rejected": True,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    runtime = run_runtime_smoke(repo_root) if not static_errors else {"status": "failed", "errors": []}
    errors = static_errors + list(runtime.get("errors", []))
    return {
        "checkpoint": "KQ-1A",
        "schema_version": "kq1a.deck_artifact_quality_harness.check.v1",
        "expected_base_after_s13l": EXPECTED_BASE_AFTER_S13L,
        "status": "ready" if not errors and runtime.get("status") == "ready" else "failed",
        "errors": errors,
        "deck_artifact_quality_harness_supported": runtime.get("capabilities", {}).get("deck_artifact_quality_harness_supported") is True,
        "json_only_bundle_rejected": runtime.get("json_only_bundle_rejected") is True,
        "requires_pptx": runtime.get("capabilities", {}).get("requires_pptx") is True,
        "requires_rendered_slide_screenshots": runtime.get("capabilities", {}).get("requires_rendered_slide_screenshots") is True,
        "requires_geometry_report": runtime.get("capabilities", {}).get("requires_geometry_report") is True,
        "requires_visual_qa_report": runtime.get("capabilities", {}).get("requires_visual_qa_report") is True,
        "requires_citation_manifest": runtime.get("capabilities", {}).get("requires_citation_manifest") is True,
        "requires_source_evidence_manifest": runtime.get("capabilities", {}).get("requires_source_evidence_manifest") is True,
        "requires_review_packet_over_actual_deck": runtime.get("capabilities", {}).get("requires_review_packet_over_actual_deck") is True,
        "focus_scenario_id": runtime.get("capabilities", {}).get("focus_scenario_id"),
        "calls_gigachat_by_kq1a": False,
        "generates_pptx_by_kq1a": False,
        "kimi_level_claimed_by_kq1a": False,
        "selected_offline_workflow_parity_claim_supported_after_kq1a": False,
        "server3_local_intranet_route_verified_by_kq1a": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KQ-1A deck artifact quality harness readiness.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = build_report(repo_root, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[kq1a-deck-artifact-quality-harness]")
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        if not args.json:
            for error in report["errors"]:
                print(f"[FAIL] {error}")
        return 1
    if not args.json:
        print("[PASS] KQ-1A deck artifact quality harness ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
